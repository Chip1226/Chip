// Virtual Wall Street in 3D. Reads the bots' live state from city.py (/api/state)
// and draws a night city: the Exchange in the middle, one tower per bot around it.

import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const COLORS = { call: 0x33d6ff, put: 0xff4fd8, profit: 0x3ddc84, loss: 0xff5a6a, info: 0xffd84d };
const CSS = { call: '#33d6ff', put: '#ff4fd8', profit: '#3ddc84', loss: '#ff5a6a', info: '#ffd84d' };
const RING = 85;                           // bot towers stand on a circle this far from the Exchange
const TOWER_W = 16;
const TOWER_H = [48, 56, 44, 52, 46, 54];
const EXCHANGE_TOP = 168;

// ---------- Renderer, scene, camera ----------

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.FogExp2(0x0a1022, 0.0021);
const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.5, 4000);

const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloom = new UnrealBloomPass(new THREE.Vector2(window.innerWidth / 2, window.innerHeight / 2), 0.85, 0.55, 0.8);
composer.addPass(bloom);
composer.addPass(new OutputPass());

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  composer.setSize(window.innerWidth, window.innerHeight);
});

// Small seeded random generator so the city looks the same every time.
function rng(seed) {
  return () => {
    seed |= 0; seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------- Sky, sun, moon, stars, lights (day while the market is open, night when it's closed) ----------

const SKY = {
  night: { top: 0x02030a, mid: 0x0c1430, horizon: 0x3b2a55 },
  day: { top: 0x1d5cc2, mid: 0x5a9ae6, horizon: 0xcfe2f6 },
};

function makeSky(colors) {
  return new THREE.Mesh(
    new THREE.SphereGeometry(2000, 32, 16),
    new THREE.ShaderMaterial({
      side: THREE.BackSide, depthWrite: false, fog: false,
      uniforms: {
        top: { value: new THREE.Color(colors.top) },
        mid: { value: new THREE.Color(colors.mid) },
        horizon: { value: new THREE.Color(colors.horizon) },
      },
      vertexShader: `varying vec3 vDir;
        void main() { vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
      fragmentShader: `uniform vec3 top; uniform vec3 mid; uniform vec3 horizon; varying vec3 vDir;
        void main() {
          float h = vDir.y;
          vec3 c = mix(mix(horizon, mid, smoothstep(0.0, 0.18, h)), top, smoothstep(0.18, 0.85, h));
          if (h < 0.0) c = horizon * 0.5;
          gl_FragColor = vec4(c, 1.0);
        }`,
    }),
  );
}
const sky = makeSky(SKY.night);
scene.add(sky);

const stars = (() => {
  const r = rng(7), positions = [], colors = [];
  for (let i = 0; i < 2200; i++) {
    const u = r() * 2 * Math.PI, v = 0.08 + r() * 0.92;
    const y = v, s = Math.sqrt(1 - y * y);
    positions.push(Math.cos(u) * s * 1900, y * 1900, Math.sin(u) * s * 1900);
    const b = 0.4 + r() * 0.6;
    colors.push(b, b, b * (0.9 + r() * 0.2));
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));
  const points = new THREE.Points(geo, new THREE.PointsMaterial({
    size: 1.6, sizeAttenuation: false, vertexColors: true, fog: false, transparent: true, depthWrite: false }));
  scene.add(points);
  return points;
})();

// The moon rises in the east-ish sky at night; the sun crosses the other side by day.
const moon = new THREE.Mesh(new THREE.SphereGeometry(38, 32, 16),
  new THREE.MeshBasicMaterial({ color: new THREE.Color(0xe8eeff).multiplyScalar(1.6), fog: false }));
scene.add(moon);
const sun = new THREE.Mesh(new THREE.SphereGeometry(55, 32, 16),
  new THREE.MeshBasicMaterial({ color: new THREE.Color(0xfff2d6).multiplyScalar(3), fog: false }));
scene.add(sun);

const hemi = new THREE.HemisphereLight(0x5a74c8, 0x0a0a14, 0.55);
scene.add(hemi);
const skyLight = new THREE.DirectionalLight(0xa8baff, 0.9); // the moon at night, the sun by day
skyLight.castShadow = true;
skyLight.shadow.mapSize.set(2048, 2048);
Object.assign(skyLight.shadow.camera, { left: -240, right: 240, top: 240, bottom: -240, near: 1, far: 1000 });
skyLight.shadow.bias = -0.0004;
skyLight.shadow.normalBias = 0.6;
scene.add(skyLight);

// Reflections: glass and streets reflect a soft version of the sky (one map for night, one for day).
const envMaps = (() => {
  const pmrem = new THREE.PMREMGenerator(renderer);
  const build = (colors, glowLightness, glowPower) => {
    const envScene = new THREE.Scene();
    envScene.add(makeSky(colors));
    const r = rng(11);
    for (let i = 0; i < 40; i++) {
      const glow = new THREE.Mesh(new THREE.PlaneGeometry(40, 10 + r() * 30),
        new THREE.MeshBasicMaterial({ color: new THREE.Color().setHSL(0.08 + r() * 0.55, 0.5, glowLightness).multiplyScalar(glowPower), side: THREE.DoubleSide }));
      const a = r() * Math.PI * 2;
      glow.position.set(Math.cos(a) * 300, 10 + r() * 60, Math.sin(a) * 300);
      glow.lookAt(0, 30, 0);
      envScene.add(glow);
    }
    return pmrem.fromScene(envScene, 0.02).texture;
  };
  return { night: build(SKY.night, 0.5, 0.8), day: build(SKY.day, 0.7, 0.5) };
})();
scene.environment = envMaps.night;

// ---------- Ground, plaza, streets ----------

const ground = new THREE.Mesh(new THREE.PlaneGeometry(6000, 6000),
  new THREE.MeshStandardMaterial({ color: 0x0a0d16, roughness: 0.3, metalness: 0.75, envMapIntensity: 0.6 }));
ground.rotation.x = -Math.PI / 2;
ground.receiveShadow = true;
scene.add(ground);

function flat(geo, color, y, opts = {}) {
  const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.45, metalness: 0.4, ...opts }));
  mesh.rotation.x = -Math.PI / 2;
  mesh.position.y = y;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}
const glowMat = (hex, power) => new THREE.MeshBasicMaterial({ color: new THREE.Color(hex).multiplyScalar(power) });

flat(new THREE.CircleGeometry(50, 96), 0x151b2c, 0.04);
const plazaRing = new THREE.Mesh(new THREE.RingGeometry(49.2, 50.2, 128), glowMat(0x3a5cff, 2.2));
plazaRing.rotation.x = -Math.PI / 2; plazaRing.position.y = 0.08; scene.add(plazaRing);
flat(new THREE.RingGeometry(RING + 16, RING + 30, 128), 0x0f131e, 0.03);

const angleOf = (i) => (i / 6) * Math.PI * 2 - Math.PI / 2;
const dashGeo = new THREE.BoxGeometry(0.5, 0.06, 3);
const dashes = new THREE.InstancedMesh(dashGeo, glowMat(0xffd27a, 1.6), 400);
const lampPosts = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.18, 0.25, 7, 6),
  new THREE.MeshStandardMaterial({ color: 0x2a3142, metalness: 0.8, roughness: 0.4 }), 120);
const lampBulbs = new THREE.InstancedMesh(new THREE.SphereGeometry(0.55, 12, 8), glowMat(0xffe0a8, 3.5), 120);
{
  const m = new THREE.Matrix4(), q = new THREE.Quaternion();
  let d = 0, l = 0;
  for (let i = 0; i < 6; i++) {
    const a = angleOf(i), dir = new THREE.Vector3(Math.cos(a), 0, Math.sin(a));
    const side = new THREE.Vector3(-dir.z, 0, dir.x);
    const street = flat(new THREE.PlaneGeometry(14, RING - 50 - 6), 0x10141f, 0.05);
    street.position.set(dir.x * (50 + (RING - 50 - 6) / 2), 0.05, dir.z * (50 + (RING - 50 - 6) / 2));
    street.rotation.z = -a - Math.PI / 2;
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), -a + Math.PI / 2);
    for (let s = 54; s < RING - 10; s += 6) {
      m.compose(new THREE.Vector3(dir.x * s, 0.08, dir.z * s), q, new THREE.Vector3(1, 1, 1));
      dashes.setMatrixAt(d++, m);
    }
    for (let s = 58; s < RING - 10; s += 12) {
      for (const k of [-1, 1]) {
        const p = dir.clone().multiplyScalar(s).addScaledVector(side, k * 8.5);
        m.makeTranslation(p.x, 3.5, p.z); lampPosts.setMatrixAt(l, m);
        m.makeTranslation(p.x, 7.2, p.z); lampBulbs.setMatrixAt(l, m); l++;
      }
    }
  }
  for (let k = 0; k < 120 && d < 400; k++) {
    const a = (k / 120) * Math.PI * 2;
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), -a);
    m.compose(new THREE.Vector3(Math.cos(a) * (RING + 23), 0.08, Math.sin(a) * (RING + 23)), q, new THREE.Vector3(1, 1, 1));
    dashes.setMatrixAt(d++, m);
  }
  dashes.count = d; lampPosts.count = l; lampBulbs.count = l;
  scene.add(dashes, lampPosts, lampBulbs);
}

// ---------- Buildings ----------

const colliders = []; // {x, z, hw, hd, h} boxes the camera can't fly into

function windowTexture(seed, { cols = 8, rows = 24, lit = 0.55, tint = true } = {}) {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 512;
  const g = c.getContext('2d');
  g.fillStyle = '#05070c';
  g.fillRect(0, 0, 256, 512);
  const r = rng(seed), cw = 256 / cols, rh = 512 / rows;
  for (let y = 0; y < rows; y++) {
    for (let x = 0; x < cols; x++) {
      if (r() < lit) {
        const b = 0.35 + 0.65 * r();
        // Tinted windows for the background city; white ones for bot towers, which get colored by trade state.
        const warm = r() < 0.65;
        const [R, G, B] = !tint ? [255, 255, 255] : warm ? [255, 214, 160] : [175, 210, 255];
        g.fillStyle = `rgb(${R * b | 0},${G * b | 0},${B * b | 0})`;
      } else {
        g.fillStyle = '#121722';
      }
      g.fillRect(x * cw + cw * 0.16, y * rh + rh * 0.2, cw * 0.68, rh * 0.58);
    }
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return t;
}

const windowMats = [];
const roofMat = new THREE.MeshStandardMaterial({ color: 0x11151f, roughness: 0.7, metalness: 0.5 });

function towerMaterials(tex, w, h, emissive, intensity) {
  tex.repeat.set(w / 16, h / 77);
  const side = new THREE.MeshStandardMaterial({
    color: 0x18202e, roughness: 0.12, metalness: 0.9, envMapIntensity: 1.1,
    emissive, emissiveMap: tex, emissiveIntensity: intensity,
  });
  side.userData.base = intensity;
  side.userData.dayGlow = 0.12; // by day, windows mostly look dark against the sunlit glass
  windowMats.push(side);
  return { side, list: [side, side, roofMat, roofMat, side, side] };
}

function addBox(w, h, d, x, y, z, materials, shadows = true) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), materials);
  mesh.position.set(x, y + h / 2, z);
  mesh.castShadow = shadows;
  mesh.receiveShadow = true;
  scene.add(mesh);
  return mesh;
}

// Background skyline, in three height classes so window sizes stay right per class.
{
  const r = rng(42), classes = [[14, 34], [34, 72], [72, 130]];
  const spots = [];
  while (spots.length < 230) {
    const a = r() * Math.PI * 2, dist = 150 + Math.pow(r(), 0.7) * 420;
    const x = Math.cos(a) * dist, z = Math.sin(a) * dist, w = 10 + r() * 16, d = 10 + r() * 16;
    if (spots.some((s) => Math.abs(s.x - x) < (s.w + w) / 2 + 4 && Math.abs(s.z - z) < (s.d + d) / 2 + 4)) continue;
    const cls = dist < 230 ? (r() < 0.6 ? 0 : 1) : (r() < 0.45 ? 1 : 2);
    const [lo, hi] = classes[cls];
    spots.push({ x, z, w, d, h: lo + r() * (hi - lo), cls });
  }
  classes.forEach(([lo, hi], cls) => {
    const group = spots.filter((s) => s.cls === cls);
    const { list } = towerMaterials(windowTexture(100 + cls, { lit: 0.42 }), 18, (lo + hi) / 2, 0xffffff, 1.15);
    const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), list, group.length);
    const m = new THREE.Matrix4();
    group.forEach((s, i) => {
      m.compose(new THREE.Vector3(s.x, s.h / 2, s.z), new THREE.Quaternion(), new THREE.Vector3(s.w, s.h, s.d));
      mesh.setMatrixAt(i, m);
      colliders.push({ x: s.x, z: s.z, hw: s.w / 2, hd: s.d / 2, h: s.h });
    });
    mesh.receiveShadow = true;
    scene.add(mesh);
  });
}

// Text on a canvas, for labels and the Exchange screens.
function canvasTexture(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = renderer.capabilities.getMaxAnisotropy();
  return { c, g: c.getContext('2d'), t };
}
function roundRect(g, x, y, w, h, r) {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r);
  g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
}
const money = (v) => `${v >= 0 ? '+' : '-'}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
const pnlCss = (v) => (v > 0.005 ? CSS.profit : v < -0.005 ? CSS.loss : '#c8d0e0');

class BotTower {
  constructor(i) {
    this.i = i;
    this.h = TOWER_H[i];
    const a = angleOf(i);
    this.dir = new THREE.Vector3(Math.cos(a), 0, Math.sin(a));
    this.pos = this.dir.clone().multiplyScalar(RING);
    const mats = towerMaterials(windowTexture(20 + i, { lit: 0.6, tint: false }), TOWER_W, this.h, 0xffe2b8, 1.0);
    this.mat = mats.side;
    this.mat.userData.dayGlow = 0.55; // bot towers keep their call/put color visible by day
    addBox(TOWER_W, this.h, TOWER_W, this.pos.x, 0, this.pos.z, mats.list);
    colliders.push({ x: this.pos.x, z: this.pos.z, hw: TOWER_W / 2, hd: TOWER_W / 2, h: this.h + 12 });
    // Glowing band around the roof: green in profit, red in loss.
    this.crownMat = glowMat(0x8090b0, 1.5);
    addBox(TOWER_W + 0.8, 1.0, TOWER_W + 0.8, this.pos.x, this.h - 2.5, this.pos.z, this.crownMat, false);
    addBox(TOWER_W * 0.5, 3, TOWER_W * 0.5, this.pos.x, this.h, this.pos.z, roofMat);
    addBox(0.5, 9, 0.5, this.pos.x, this.h + 3, this.pos.z, roofMat, false);
    this.beacon = new THREE.Mesh(new THREE.SphereGeometry(0.7, 12, 8), glowMat(0xff2a2a, 4));
    this.beacon.position.set(this.pos.x, this.h + 12.4, this.pos.z);
    scene.add(this.beacon);
    this.roof = new THREE.Vector3(this.pos.x, this.h + 3, this.pos.z);

    this.label = canvasTexture(640, 400);
    this.sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: this.label.t, fog: false, transparent: true }));
    this.sprite.scale.set(32, 20, 1);
    this.sprite.position.set(this.pos.x, this.h + 21, this.pos.z);
    this.sprite.renderOrder = 10;
    scene.add(this.sprite);
    this.labelKey = '';
  }

  update(bot) {
    const kind = bot.position?.kind;
    const target = kind ? new THREE.Color(COLORS[kind]) : new THREE.Color(0xffe2b8);
    this.mat.emissive.copy(target);
    this.mat.userData.base = kind ? 1.7 : 0.9;
    this.crownMat.color.set(bot.pnl > 0.005 ? COLORS.profit : bot.pnl < -0.005 ? COLORS.loss : 0x8090b0).multiplyScalar(2.4);
    const key = JSON.stringify([bot.pnl, bot.note, bot.cash, bot.wins, bot.trades, kind]);
    if (key !== this.labelKey) { this.labelKey = key; this.drawLabel(bot); }
  }

  drawLabel(bot) {
    const { g, c, t } = this.label;
    g.clearRect(0, 0, c.width, c.height);
    roundRect(g, 8, 8, c.width - 16, c.height - 16, 26);
    g.fillStyle = 'rgba(8, 12, 24, 0.78)'; g.fill();
    g.lineWidth = 5; g.strokeStyle = bot.position ? CSS[bot.position.kind] : 'rgba(120,160,255,0.45)'; g.stroke();
    g.textAlign = 'center';
    g.fillStyle = '#d8dff0'; g.font = 'bold 54px system-ui, sans-serif';
    g.fillText(`${this.i + 1}  ${bot.name}`, c.width / 2, 78);
    g.fillStyle = pnlCss(bot.pnl); g.font = 'bold 72px system-ui, sans-serif';
    g.fillText(money(bot.pnl), c.width / 2, 162);
    g.fillStyle = '#93a0be'; g.font = '32px system-ui, sans-serif';
    g.fillText(`${bot.symbol} ${bot.style} | ${bot.signal}`, c.width / 2, 222);
    g.fillStyle = bot.position ? '#e6c84a' : '#93a0be';
    g.fillText(bot.note.length > 34 ? bot.note.slice(0, 33) + '…' : bot.note, c.width / 2, 274);
    g.fillStyle = '#93a0be';
    g.fillText(`cash $${Math.round(bot.cash).toLocaleString()} | ${bot.wins}/${bot.trades} wins`, c.width / 2, 326);
    t.needsUpdate = true;
  }
}
const towers = [0, 1, 2, 3, 4, 5].map((i) => new BotTower(i));

// The Exchange: the tall tower in the middle, with screens showing every bot's P/L.
const exchange = {};
{
  const tex = () => windowTexture(9, { lit: 0.7 });
  addBox(28, 80, 28, 0, 0, 0, towerMaterials(tex(), 28, 80, 0xffffff, 1.25).list);
  addBox(21, 36, 21, 0, 80, 0, towerMaterials(tex(), 21, 36, 0xffffff, 0.5).list);
  addBox(14, 18, 14, 0, 116, 0, towerMaterials(tex(), 14, 18, 0xffffff, 1.25).list);
  const spire = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 1.6, 34, 12),
    new THREE.MeshStandardMaterial({ color: 0x9aa6c0, metalness: 1, roughness: 0.2 }));
  spire.position.y = 134 + 17; spire.castShadow = true; scene.add(spire);
  const tip = new THREE.Mesh(new THREE.SphereGeometry(1.4, 16, 10), glowMat(0xffffff, 5));
  tip.position.y = EXCHANGE_TOP; scene.add(tip);
  colliders.push({ x: 0, z: 0, hw: 14, hd: 14, h: 80 }, { x: 0, z: 0, hw: 10.5, hd: 10.5, h: 116 },
    { x: 0, z: 0, hw: 7, hd: 7, h: 134 }, { x: 0, z: 0, hw: 2, hd: 2, h: EXCHANGE_TOP + 2 });

  // Four screens wrapped around the middle section, one per side.
  exchange.screen = canvasTexture(640, 1100);
  const screenMat = new THREE.MeshBasicMaterial({ map: exchange.screen.t, fog: false });
  for (let k = 0; k < 4; k++) {
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(19.5, 33.5), screenMat);
    const a = (k * Math.PI) / 2;
    plane.position.set(Math.sin(a) * 10.56, 98, Math.cos(a) * 10.56);
    plane.rotation.y = a;
    scene.add(plane);
  }
  // A halo ring floating around the tower: green when the bots are up overall, red when down.
  exchange.haloMat = glowMat(0x8090b0, 2);
  exchange.halo = new THREE.Mesh(new THREE.TorusGeometry(24, 0.45, 12, 160), exchange.haloMat);
  exchange.halo.position.y = 64;
  exchange.halo.rotation.x = Math.PI / 2;
  scene.add(exchange.halo);
  exchange.key = '';

  // Six light columns on the plaza, one pointing at each bot: height = P/L as % of its budget.
  exchange.bars = towers.map((tw) => {
    const geo = new THREE.BoxGeometry(3.2, 1, 3.2);
    geo.translate(0, 0.5, 0);
    const mat = glowMat(0x8090b0, 1.4);
    const bar = new THREE.Mesh(geo, mat);
    bar.position.copy(tw.dir).multiplyScalar(36);
    bar.scale.y = 0.6;
    scene.add(bar);
    const base = new THREE.Mesh(new THREE.CylinderGeometry(3.4, 3.8, 0.8, 24), roofMat);
    base.position.copy(bar.position).setY(0.4);
    scene.add(base);
    return { bar, mat, target: 0.6 };
  });
}

function drawExchange(state) {
  const { g, c, t } = exchange.screen;
  g.fillStyle = '#060a16'; g.fillRect(0, 0, c.width, c.height);
  g.strokeStyle = 'rgba(80, 120, 255, 0.55)'; g.lineWidth = 6; g.strokeRect(10, 10, c.width - 20, c.height - 20);
  g.textAlign = 'center';
  g.fillStyle = '#7f8db0'; g.font = 'bold 34px system-ui, sans-serif';
  g.fillText('VIRTUAL WALL STREET', c.width / 2, 72);
  g.fillText('EXCHANGE', c.width / 2, 114);
  g.fillStyle = '#93a0be'; g.font = '30px system-ui, sans-serif';
  g.fillText('TOTAL P/L - ALL BOTS', c.width / 2, 200);
  g.fillStyle = pnlCss(state.total_pnl); g.font = 'bold 84px system-ui, sans-serif';
  g.fillText(money(state.total_pnl), c.width / 2, 296);
  g.fillStyle = 'rgba(120,160,255,0.35)'; g.fillRect(50, 336, c.width - 100, 3);
  state.bots.forEach((b, i) => {
    const y = 410 + i * 104;
    g.textAlign = 'left'; g.fillStyle = '#d8dff0'; g.font = 'bold 36px system-ui, sans-serif';
    g.fillText(`${i + 1} ${b.name}`, 50, y);
    g.fillStyle = '#7f8db0'; g.font = '26px system-ui, sans-serif';
    g.fillText(b.position ? `${b.position.kind.toUpperCase()} ${b.position.label}` : 'in cash', 50, y + 38);
    g.textAlign = 'right'; g.fillStyle = pnlCss(b.pnl); g.font = 'bold 38px system-ui, sans-serif';
    g.fillText(money(b.pnl), c.width - 50, y);
    g.font = '26px system-ui, sans-serif';
    g.fillText(`${(b.pnl_pct * 100).toFixed(1)}%`, c.width - 50, y + 38);
    if (b.position) {
      g.fillStyle = CSS[b.position.kind];
      g.beginPath(); g.arc(c.width - 50 - 140, y + 28, 10, 0, Math.PI * 2); g.fill();
    }
  });
  g.textAlign = 'center'; g.fillStyle = '#7f8db0'; g.font = '24px system-ui, sans-serif';
  g.fillText(state.paused ? 'TRADING PAUSED' : (state.status || '').slice(0, 44), c.width / 2, c.height - 44);
  t.needsUpdate = true;
}

// ---------- Trade beams ----------

const beams = [];
// A fixed pool of flash lights: adding and removing lights would make every material recompile.
const flashLights = [0, 1, 2, 3].map(() => {
  const light = new THREE.PointLight(0xffffff, 0, 160, 1.6);
  scene.add(light);
  return light;
});
function spawnBeam(tower, kind) {
  const color = new THREE.Color(COLORS[kind] ?? COLORS.info);
  const group = new THREE.Group();
  group.position.copy(tower.roof);
  const h = 700;
  const mk = (radius, power, opacity) => {
    const geo = new THREE.CylinderGeometry(radius, radius, h, 24, 1, true);
    geo.translate(0, h / 2, 0);
    const mat = new THREE.MeshBasicMaterial({ color: color.clone().multiplyScalar(power), transparent: true,
      opacity, blending: THREE.AdditiveBlending, depthWrite: false, fog: false, side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.userData.baseOpacity = opacity;
    group.add(mesh);
    return mesh;
  };
  mk(0.6, 4, 1); mk(1.6, 1.4, 0.35); mk(3.6, 0.6, 0.1);
  const ring = new THREE.Mesh(new THREE.RingGeometry(1.7, 2.2, 64), new THREE.MeshBasicMaterial({
    color: color.clone().multiplyScalar(3), transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2;
  ring.userData.baseOpacity = 1;
  group.add(ring);
  const light = flashLights.find((l) => !l.userData.busy) ?? flashLights[0];
  light.userData.busy = true;
  light.color.copy(color);
  light.position.copy(tower.roof).setY(tower.roof.y + 4);
  scene.add(group);
  beams.push({ group, ring, light, t: 0 });
}

function updateBeams(dt) {
  for (let i = beams.length - 1; i >= 0; i--) {
    const b = beams[i];
    b.t += dt;
    const grow = 1 - Math.pow(1 - Math.min(b.t / 0.35, 1), 3);
    const fade = b.t < 1.4 ? 1 : Math.max(0, 1 - (b.t - 1.4) / 1.8);
    b.group.children.forEach((m) => {
      if (m.isMesh && m !== b.ring) { m.scale.y = Math.max(grow, 0.001); m.material.opacity = m.userData.baseOpacity * fade; }
    });
    b.ring.scale.setScalar(1 + b.t * 11);
    b.ring.material.opacity = Math.max(0, 1 - b.t / 1.2);
    b.light.intensity = 3500 * fade * (b.t < 0.3 ? b.t / 0.3 : 1);
    if (b.t > 3.3) {
      b.light.intensity = 0;
      b.light.userData.busy = false;
      scene.remove(b.group);
      b.group.traverse((o) => { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } });
      beams.splice(i, 1);
    }
  }
}

// ---------- Moving around ----------

const nav = {
  pos: new THREE.Vector3(0, 60, 230), yaw: 0, pitch: -0.12, vel: new THREE.Vector3(),
  keys: new Set(), locked: false, travel: null, orbit: null, at: null,
};
const canvas = renderer.domElement;

function lookAngles(from, to) {
  const d = to.clone().sub(from).normalize();
  return { yaw: Math.atan2(-d.x, -d.z), pitch: Math.asin(THREE.MathUtils.clamp(d.y, -1, 1)) };
}

// Index 0-5 = bot towers, 6 = the Exchange. Each has a viewpoint and a point to look at.
function viewOf(index) {
  // The Exchange: face its +X screen head-on, from the gap between bot towers 1 and 2.
  if (index === 6) return { eye: new THREE.Vector3(62, 96, 0), look: new THREE.Vector3(0, 97, 0), center: new THREE.Vector3(0, 90, 0), radius: 120 };
  const tw = towers[index];
  // From outside the ring looking in, so the Exchange stands behind the tower.
  return {
    eye: tw.pos.clone().addScaledVector(tw.dir, 92).setY(tw.h * 0.6 + 8),
    look: tw.pos.clone().setY(tw.h * 0.8 + 4),
    center: tw.pos.clone().setY(tw.h * 0.8 + 4), radius: 92,
  };
}

function travelTo(index, instant = false) {
  const v = viewOf(index);
  nav.orbit = null;
  nav.at = index;
  const end = lookAngles(v.eye, v.look);
  if (instant) {
    nav.pos.copy(v.eye); nav.yaw = end.yaw; nav.pitch = end.pitch; nav.travel = null;
  } else {
    const p0 = nav.pos.clone(), p1 = v.eye.clone(), dist = p0.distanceTo(p1);
    const mid = p0.clone().add(p1).multiplyScalar(0.5);
    // Arc up and, if the straight path would cut through the Exchange, swing around it.
    const seg = p1.clone().sub(p0).setY(0), toO = p0.clone().setY(0).negate();
    const tProj = THREE.MathUtils.clamp(toO.dot(seg) / Math.max(seg.lengthSq(), 1e-6), 0, 1);
    const closest = p0.clone().setY(0).addScaledVector(seg, tProj);
    if (closest.length() < 45) {
      const side = new THREE.Vector3(-seg.z, 0, seg.x).normalize();
      if (side.dot(mid.clone().setY(0)) < 0) side.negate();
      mid.x = side.x * 150; mid.z = side.z * 150;
    }
    mid.y = Math.max(p0.y, p1.y) + 30 + dist * 0.12;
    nav.travel = { p0, ctrl: mid, p1, y0: nav.yaw, p0p: nav.pitch, end, t: 0, dur: THREE.MathUtils.clamp(dist / 110, 1.4, 3.2) };
  }
  hideHint();
}

function toggleOrbit() {
  if (nav.orbit) { nav.orbit = null; return; }
  if (nav.at == null) { // pick the nearest building
    let best = 6, bestD = nav.pos.length();
    towers.forEach((tw, i) => { const d = nav.pos.distanceTo(tw.pos); if (d < bestD) { bestD = d; best = i; } });
    nav.at = best;
  }
  const v = viewOf(nav.at);
  const off = nav.pos.clone().sub(v.center).setY(0);
  nav.travel = null;
  nav.orbit = { center: v.center, radius: v.radius, angle: Math.atan2(off.z, off.x), height: Math.max(nav.pos.y, v.center.y) };
}

const hint = document.getElementById('hint');
function hideHint() { hint.style.opacity = '0'; }

let dragged = false;
canvas.addEventListener('mousedown', () => { dragged = false; });
canvas.addEventListener('mousemove', (e) => {
  if (nav.locked || e.buttons === 1) {
    if (!nav.locked) dragged = true;
    nav.yaw -= e.movementX * 0.0022;
    nav.pitch = THREE.MathUtils.clamp(nav.pitch - e.movementY * 0.0022, -1.45, 1.45);
    if (nav.travel || nav.orbit) { nav.travel = null; nav.orbit = null; }
  }
});
canvas.addEventListener('click', () => { if (!dragged && !nav.locked) canvas.requestPointerLock(); });
document.addEventListener('pointerlockchange', () => {
  nav.locked = document.pointerLockElement === canvas;
  document.getElementById('crosshair').style.display = nav.locked ? 'block' : 'none';
  if (nav.locked) hideHint();
});

const MOVE_KEYS = new Set(['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'KeyE', 'KeyQ', 'KeyC']);
window.addEventListener('keydown', (e) => {
  if (e.target.closest && e.target.closest('button')) e.target.blur();
  if (e.code === 'Tab') { e.preventDefault(); travelTo(((nav.at ?? 6) + 1) % 7); return; }
  if (/^Digit[0-6]$/.test(e.code)) { const n = +e.code.slice(5); travelTo(n === 0 ? 6 : n - 1); return; }
  if (e.code === 'KeyR') { toggleOrbit(); return; }
  if (e.code === 'KeyP') { togglePause(); return; }
  if (e.code === 'KeyN') { cycleDaylight(); return; }
  if (e.code === 'KeyH') { document.getElementById('legend').classList.toggle('hidden'); return; }
  if (MOVE_KEYS.has(e.code)) {
    e.preventDefault();
    nav.keys.add(e.code);
    nav.travel = null; nav.orbit = null; nav.at = null;
    hideHint();
  }
  if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') nav.keys.add('Shift');
});
window.addEventListener('keyup', (e) => {
  nav.keys.delete(e.code);
  if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') nav.keys.delete('Shift');
});
window.addEventListener('blur', () => nav.keys.clear());

function collide(p) {
  for (const b of colliders) {
    if (p.y > b.h + 2) continue;
    const dx = p.x - b.x, dz = p.z - b.z, ox = b.hw + 2.5 - Math.abs(dx), oz = b.hd + 2.5 - Math.abs(dz);
    if (ox > 0 && oz > 0) {
      const oy = b.h + 2 - p.y; // climbing over the roof may be the shortest way out
      if (oy < ox && oy < oz) p.y += oy;
      else if (ox < oz) p.x += Math.sign(dx || 1) * ox;
      else p.z += Math.sign(dz || 1) * oz;
    }
  }
  p.y = THREE.MathUtils.clamp(p.y, 2, 500);
  const r = Math.hypot(p.x, p.z);
  if (r > 900) { p.x *= 900 / r; p.z *= 900 / r; }
}

const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
function shortAngle(a, b) { let d = (b - a) % (Math.PI * 2); if (d > Math.PI) d -= Math.PI * 2; if (d < -Math.PI) d += Math.PI * 2; return d; }

function updateNav(dt) {
  if (nav.travel) {
    const tr = nav.travel;
    tr.t += dt / tr.dur;
    const t = easeInOut(Math.min(tr.t, 1)), u = 1 - t;
    nav.pos.set(0, 0, 0).addScaledVector(tr.p0, u * u).addScaledVector(tr.ctrl, 2 * u * t).addScaledVector(tr.p1, t * t);
    nav.yaw = tr.y0 + shortAngle(tr.y0, tr.end.yaw) * t;
    nav.pitch = tr.p0p + (tr.end.pitch - tr.p0p) * t;
    if (tr.t >= 1) nav.travel = null;
  } else if (nav.orbit) {
    const o = nav.orbit;
    o.angle += dt * 0.22;
    nav.pos.set(o.center.x + Math.cos(o.angle) * o.radius, o.height, o.center.z + Math.sin(o.angle) * o.radius);
    const ang = lookAngles(nav.pos, o.center);
    nav.yaw = ang.yaw; nav.pitch = ang.pitch;
  } else {
    const k = nav.keys, speed = k.has('Shift') ? 130 : 45;
    const fwd = new THREE.Vector3(-Math.sin(nav.yaw) * Math.cos(nav.pitch), Math.sin(nav.pitch), -Math.cos(nav.yaw) * Math.cos(nav.pitch));
    const right = new THREE.Vector3(Math.cos(nav.yaw), 0, -Math.sin(nav.yaw));
    const want = new THREE.Vector3();
    // Arrow keys: walk forward/back at the current height and turn left/right (keyboard only).
    const level = new THREE.Vector3(-Math.sin(nav.yaw), 0, -Math.cos(nav.yaw));
    if (k.has('ArrowLeft')) nav.yaw += dt * 1.7;
    if (k.has('ArrowRight')) nav.yaw -= dt * 1.7;
    if (k.has('ArrowUp')) want.add(level);
    if (k.has('ArrowDown')) want.sub(level);
    // W A S D: fly wherever you're looking (up and down included).
    if (k.has('KeyW')) want.add(fwd);
    if (k.has('KeyS')) want.sub(fwd);
    if (k.has('KeyD')) want.add(right);
    if (k.has('KeyA')) want.sub(right);
    if (k.has('Space') || k.has('KeyE')) want.y += 1;
    if (k.has('KeyQ') || k.has('KeyC')) want.y -= 1;
    if (want.lengthSq() > 0) want.normalize().multiplyScalar(speed);
    nav.vel.lerp(want, 1 - Math.exp(-dt * 6));
    nav.pos.addScaledVector(nav.vel, dt);
    collide(nav.pos);
  }
  camera.position.copy(nav.pos);
  camera.rotation.set(nav.pitch, nav.yaw, 0, 'YXZ');
}

// ---------- Live state from the trading engine ----------

const el = (id) => document.getElementById(id);
let lastEventId = null;

function buildingList(state) {
  const box = el('buildings');
  if (box.childElementCount !== state.bots.length + 1) {
    box.innerHTML = '';
    const add = (key, index) => {
      const btn = document.createElement('button');
      btn.innerHTML = `<span class="key">${key}</span><span class="name"></span><span class="pnl"></span>`;
      btn.addEventListener('click', () => { travelTo(index); btn.blur(); });
      box.appendChild(btn);
    };
    add('0', 6);
    state.bots.forEach((_, i) => add(String(i + 1), i));
  }
  const rows = box.children;
  const set = (btn, name, pnl, index) => {
    btn.querySelector('.name').textContent = name;
    const p = btn.querySelector('.pnl');
    p.textContent = money(pnl);
    p.style.color = pnlCss(pnl);
    btn.classList.toggle('here', nav.at === index);
  };
  set(rows[0], 'Exchange (total)', state.total_pnl, 6);
  state.bots.forEach((b, i) => set(rows[i + 1], b.name, b.pnl, i));
}

const feedItems = [];
function addFeed(e) {
  feedItems.unshift(e);
  feedItems.length = Math.min(feedItems.length, 7);
  el('feedItems').innerHTML = feedItems.map((f) =>
    `<div class="item"><span style="color:${CSS[f.kind] || CSS.info}">${f.text}</span> <span style="color:var(--muted)">${f.bot}</span></div>`).join('');
}

function applyState(s) {
  daylight.market = s.market_open;
  if (!daylight.ready && s.market_open !== null) { // first reading: jump straight there, no sunset on load
    daylight.ready = true;
    if (daylight.override === 'auto') daylight.t = s.market_open ? 1 : 0;
  }
  el('skyLine').innerHTML = skyText();
  el('mode').textContent = s.mode;
  let status = s.status || '';
  if (s.equity != null) status += `  |  Paper equity $${s.equity.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
  el('statusLine').innerHTML = (s.paused ? '<span class="paused">TRADING PAUSED (P to resume)</span><br>' : '') + status;
  if (s.news) {
    const v = s.news.latest[s.news.latest.length - 1];
    el('newsLine').textContent = `News: ${s.news.calls} judged, $${s.news.spent.toFixed(4)}` +
      (v ? `  |  ${v.symbol} ${v.direction.toUpperCase()} (${v.strength}, ${v.time}): ${v.reason}` : '');
  } else el('newsLine').textContent = '';
  el('errorLine').textContent = s.error || '';
  const total = el('totalValue');
  total.textContent = money(s.total_pnl);
  total.style.color = pnlCss(s.total_pnl);
  buildingList(s);

  s.bots.forEach((b, i) => {
    if (!towers[i]) return;
    towers[i].update(b);
    const bar = exchange.bars[i];
    bar.target = THREE.MathUtils.clamp(Math.abs(b.pnl_pct) * 80, 0.6, 46);
    bar.mat.color.set(b.pnl > 0.005 ? COLORS.profit : b.pnl < -0.005 ? COLORS.loss : 0x8090b0).multiplyScalar(1.6);
  });
  exchange.haloMat.color.set(s.total_pnl > 0.005 ? COLORS.profit : s.total_pnl < -0.005 ? COLORS.loss : 0x8090b0).multiplyScalar(2.2);
  const key = JSON.stringify([s.total_pnl, s.paused, s.status, s.bots.map((b) => [b.pnl, b.position])]);
  if (key !== exchange.key) { exchange.key = key; drawExchange(s); }

  const firstLoad = lastEventId === null;
  for (const e of s.events) {
    addFeed(e);
    const i = s.bots.findIndex((b) => b.name === e.bot);
    if (!firstLoad && i >= 0 && towers[i]) spawnBeam(towers[i], e.kind);
  }
  lastEventId = s.last_event_id;
}

let stopped = false;
async function poll() {
  if (stopped) return;
  try {
    const r = await fetch(`/api/state?since=${lastEventId ?? 0}`);
    applyState(await r.json());
    el('offline').style.display = 'none';
  } catch (err) {
    el('offline').style.display = 'block';
  }
  setTimeout(poll, 500);
}

document.getElementById('stopBtn').addEventListener('click', async (e) => {
  e.currentTarget.blur();
  if (!window.confirm('Stop the game? The bots stop trading until you open it again.')) return;
  try {
    await fetch('/api/quit', { method: 'POST', headers: { 'X-VWS': '1' } });
    stopped = true;
    el('offline').style.display = 'none';
    el('stopped').style.display = 'block';
  } catch (err) { /* poll shows the connection problem */ }
});

async function togglePause() {
  try { await fetch('/api/pause', { method: 'POST', headers: { 'X-VWS': '1' } }); } catch (err) { /* shown by poll */ }
}


// ---------- Day and night ----------
// 1 = full day, 0 = full night. Follows the market: open = day, closed = night.
// N cycles a preview: follow the market -> always day -> always night.

const daylight = { t: 0, target: 0, market: null, override: 'auto', ready: false };
const lampBase = lampBulbs.material.color.clone();
const dashBase = dashes.material.color.clone();
const C = (hex) => new THREE.Color(hex);
const LOOK = {
  night: { fog: C(0x0a1022), fogDensity: 0.0021, hemiSky: C(0x5a74c8), hemiGround: C(0x0a0a14), hemi: 0.55,
    exposure: 1.05, bloom: 0.85, threshold: 0.8, lamps: 1, sky: { top: C(SKY.night.top), mid: C(SKY.night.mid), horizon: C(SKY.night.horizon) } },
  day: { fog: C(0xb9cde6), fogDensity: 0.0011, hemiSky: C(0xd2e6ff), hemiGround: C(0x4a4f5a), hemi: 1.7,
    exposure: 0.95, bloom: 0.3, threshold: 0.95, lamps: 0.12, sky: { top: C(SKY.day.top), mid: C(SKY.day.mid), horizon: C(SKY.day.horizon) } },
};
const smooth = (a, b, x) => { const t = THREE.MathUtils.clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

function setDaylight(t) {
  const n = LOOK.night, d = LOOK.day;
  for (const k of ['top', 'mid', 'horizon']) sky.material.uniforms[k].value.copy(n.sky[k]).lerp(d.sky[k], t);
  scene.fog.color.copy(n.fog).lerp(d.fog, t);
  scene.fog.density = THREE.MathUtils.lerp(n.fogDensity, d.fogDensity, t);
  hemi.color.copy(n.hemiSky).lerp(d.hemiSky, t);
  hemi.groundColor.copy(n.hemiGround).lerp(d.hemiGround, t);
  hemi.intensity = THREE.MathUtils.lerp(n.hemi, d.hemi, t);
  renderer.toneMappingExposure = THREE.MathUtils.lerp(n.exposure, d.exposure, t);
  bloom.strength = THREE.MathUtils.lerp(n.bloom, d.bloom, t);
  bloom.threshold = THREE.MathUtils.lerp(n.threshold, d.threshold, t);
  scene.environment = t > 0.5 ? envMaps.day : envMaps.night;
  ground.material.roughness = THREE.MathUtils.lerp(0.3, 0.7, t); // wet-look streets at night, dry by day

  // The sun climbs as day comes; the moon rises as night falls.
  const sunDir = new THREE.Vector3(0.45, THREE.MathUtils.lerp(-0.3, 0.4, t), -0.85).normalize();
  const moonDir = new THREE.Vector3(-0.55, THREE.MathUtils.lerp(0.42, -0.3, t), -0.72).normalize();
  sun.position.copy(sunDir).multiplyScalar(1750);
  moon.position.copy(moonDir).multiplyScalar(1700);
  sun.visible = sunDir.y > -0.08;
  moon.visible = moonDir.y > -0.08;
  stars.material.opacity = Math.pow(1 - smooth(0, 0.6, t), 2);
  const sunUp = smooth(0.35, 0.9, t), moonUp = smooth(0.35, 0.9, 1 - t);
  if (sunUp >= moonUp) {
    skyLight.position.copy(sunDir).multiplyScalar(400);
    skyLight.color.set(0xfff0d8);
    skyLight.intensity = 2.6 * sunUp;
  } else {
    skyLight.position.copy(moonDir).multiplyScalar(400);
    skyLight.color.set(0xa8baff);
    skyLight.intensity = 0.9 * moonUp;
  }

  for (const m of windowMats) m.emissiveIntensity = m.userData.base * THREE.MathUtils.lerp(1, m.userData.dayGlow, t);
  const lamps = THREE.MathUtils.lerp(n.lamps, d.lamps, t);
  lampBulbs.material.color.copy(lampBase).multiplyScalar(lamps);
  dashes.material.color.copy(dashBase).multiplyScalar(Math.max(lamps, 0.35));
}

function updateDaylight(dt) {
  const o = daylight.override;
  daylight.target = o === 'day' ? 1 : o === 'night' ? 0 : daylight.market === true ? 1 : 0;
  const step = dt / 6; // a full sunset or sunrise takes about 6 seconds
  daylight.t += THREE.MathUtils.clamp(daylight.target - daylight.t, -step, step);
  setDaylight(daylight.t);
}

function skyText() {
  const night = daylight.target < 0.5;
  const what = daylight.override === 'auto'
    ? (daylight.market === null ? 'Waiting for the market clock' : night ? 'Market closed: night' : 'Market open: daytime')
    : `Preview: always ${daylight.override} (N to follow the market)`;
  return `${night ? '&#9790;' : '&#9728;'} ${what}`;
}

function cycleDaylight() {
  daylight.override = { auto: 'day', day: 'night', night: 'auto' }[daylight.override];
  el('skyLine').innerHTML = skyText();
}

// ---------- Main loop ----------

const clock = new THREE.Clock();
function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  const time = clock.elapsedTime;
  updateNav(dt);
  updateBeams(dt);
  updateDaylight(dt);
  exchange.halo.rotation.z += dt * 0.15;
  exchange.halo.position.y = 64 + Math.sin(time * 0.6) * 1.5;
  for (const b of exchange.bars) b.bar.scale.y += (b.target - b.bar.scale.y) * (1 - Math.exp(-dt * 3));
  const blink = (Math.sin(time * 3) + 1) / 2 > 0.75 ? 4 : 0.4;
  towers.forEach((tw) => tw.beacon.material.color.setRGB(blink, 0.1 * blink, 0.1 * blink));
  const rows = el('buildings').children;
  for (let i = 0; i < rows.length; i++) rows[i].classList.toggle('here', nav.at === (i === 0 ? 6 : i - 1));
  composer.render();
  requestAnimationFrame(frame);
}

travelTo(6, true);
nav.pos.set(0, 70, 240);
{ const a = lookAngles(nav.pos, new THREE.Vector3(0, 70, 0)); nav.yaw = a.yaw; nav.pitch = a.pitch; }
nav.at = null;
poll();
frame();

// Handy for testing from the browser console, e.g. vws.travelTo(2, true)
window.vws = { daylight, travelTo, spawnBeam: (i, kind) => spawnBeam(towers[i], kind), nav, camera,
  collide: (x, y, z) => { const p = new THREE.Vector3(x, y, z); collide(p); return p; } };

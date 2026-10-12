import Header from "@/components/Header";
import Hero from "@/components/Hero";
import Problem from "@/components/Problem";
import HowItWorks from "@/components/HowItWorks";
import Trades from "@/components/Trades";
import Pricing from "@/components/Pricing";
import Faq from "@/components/Faq";
import DemoForm from "@/components/DemoForm";
import Footer from "@/components/Footer";

export default function Home() {
  return (
    <>
      <Header />
      <main>
        <Hero />
        <Problem />
        <HowItWorks />
        <Trades />
        <Pricing />
        <Faq />
        <DemoForm />
      </main>
      <Footer />
    </>
  );
}

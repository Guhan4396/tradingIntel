import HeroSection from "@/components/landing/HeroSection";
import FeaturesSection from "@/components/landing/FeaturesSection";

export default function LandingPage() {
  return (
    <main>
      <div id="hero">
        <HeroSection />
      </div>
      <FeaturesSection />
    </main>
  );
}

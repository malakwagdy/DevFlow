import Page from '../components/layout/Page';
import AsyncContent from '../components/ui/AsyncContent';
import CapabilitiesSection from '../components/landing/CapabilitiesSection';
import CtaBand from '../components/landing/CtaBand';
import FaqSection from '../components/landing/FaqSection';
import HeroSection from '../components/landing/HeroSection';
import HowItWorksSection from '../components/landing/HowItWorksSection';
import PricingSection from '../components/landing/PricingSection';
import SiteFooter from '../components/landing/SiteFooter';
import useApi from '../hooks/useApi';
import { api } from '../services/api';

export default function LandingPage() {
  const state = useApi(api.getLandingContent);

  return (
    <Page>
      <AsyncContent state={state}>
        {(content) => (
          <>
            <HeroSection hero={content.hero} preview={content.preview} />
            <HowItWorksSection id="how-it-works" {...content.howItWorks} />
            <CapabilitiesSection id="capabilities" {...content.capabilities} />
            <PricingSection id="comparison" {...content.tiers} />
            <FaqSection id="faq" {...content.faq} />
            <CtaBand {...content.cta} />
            <SiteFooter {...content.footer} />
          </>
        )}
      </AsyncContent>
    </Page>
  );
}

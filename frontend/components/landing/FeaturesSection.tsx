const features = [
  {
    icon: "🔔",
    title: "4-Hour Alert Delivery",
    description:
      "We monitor USTR, EU TARIC, UK HMRC, DGFT, CBIC and 5 more sources. When something affects your HSN codes and markets, you get a WhatsApp alert in under 4 hours.",
  },
  {
    icon: "⚡",
    title: "15-Second Pre-Shipment Check",
    description:
      "Before every shipment, check tariff rates, FTA eligibility, duty calculation, and required documents in 15 seconds. Avoid costly mistakes at the port.",
  },
  {
    icon: "🤖",
    title: "AI Intelligence Processing",
    description:
      "Claude AI reads and interprets every regulatory update, extracting what matters for YOUR specific HSN codes and markets — not generic news.",
  },
  {
    icon: "📱",
    title: "WhatsApp-First Delivery",
    description:
      "Receive intelligence directly on WhatsApp. Run shipment checks by messaging us. No new app to learn — trade intelligence where your team already works.",
  },
  {
    icon: "🗺️",
    title: "FTA Benefits Maximizer",
    description:
      "India has 13+ active FTAs. We track which ones apply to your products and alert you when you can save on duties — with exact steps to claim benefits.",
  },
  {
    icon: "📊",
    title: "Weekly Market Digest",
    description:
      "Every Monday, receive a curated digest of the week's most important trade developments for your specific product categories and export markets.",
  },
];

const pricing = [
  {
    name: "Pilot",
    price: "₹7,500",
    period: "/month",
    description: "For exporters just starting out",
    features: [
      "5 HSN codes tracked",
      "3 destination markets",
      "Weekly digest",
      "WhatsApp alerts",
      "10 pre-shipment checks/month",
    ],
    cta: "Start Pilot",
    highlighted: false,
  },
  {
    name: "Monthly",
    price: "₹15,000",
    period: "/month",
    description: "For growing export businesses",
    features: [
      "20 HSN codes tracked",
      "10 destination markets",
      "Daily alerts",
      "WhatsApp + Email",
      "Unlimited shipment checks",
      "Priority support",
    ],
    cta: "Start Free Trial",
    highlighted: true,
  },
  {
    name: "Annual",
    price: "₹1,50,000",
    period: "/year",
    description: "Best value — save 2 months",
    features: [
      "Unlimited HSN codes",
      "All markets",
      "Real-time alerts",
      "All channels",
      "Unlimited checks",
      "Dedicated account manager",
      "API access",
    ],
    cta: "Contact Sales",
    highlighted: false,
  },
];

export default function FeaturesSection() {
  return (
    <>
      {/* Features */}
      <section className="bg-[#0F172A] py-24 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">
              Everything Your Export Team Needs
            </h2>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              From regulatory alerts to pre-shipment checks — TradingIntel covers
              the full trade intelligence lifecycle.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="bg-slate-800/50 border border-slate-700 rounded-2xl p-8 hover:border-amber-500/30 transition-all duration-300 hover:bg-slate-800"
              >
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-bold text-white mb-3">{feature.title}</h3>
                <p className="text-slate-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Social proof */}
      <section className="bg-slate-800/30 py-16 px-4 border-y border-slate-700/50">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-slate-400 text-lg mb-8">
            Trusted by exporters across India's textile hubs
          </p>
          <div className="flex flex-wrap justify-center gap-8 text-slate-500 text-sm">
            {["Surat", "Tiruppur", "Ludhiana", "Bhiwandi", "Panipat", "Erode"].map((city) => (
              <span key={city} className="flex items-center gap-2">
                <span className="w-2 h-2 bg-amber-500 rounded-full" />
                {city}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section className="bg-[#0F172A] py-24 px-4" id="pricing">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-slate-400">
              Start with a 30-day free trial. No credit card required.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricing.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-2xl p-8 border ${
                  plan.highlighted
                    ? "bg-amber-500/10 border-amber-500 shadow-lg shadow-amber-500/10"
                    : "bg-slate-800/50 border-slate-700"
                }`}
              >
                {plan.highlighted && (
                  <div className="text-xs font-semibold text-amber-400 bg-amber-400/10 px-3 py-1 rounded-full inline-block mb-4">
                    MOST POPULAR
                  </div>
                )}
                <h3 className="text-xl font-bold text-white">{plan.name}</h3>
                <div className="mt-4 mb-6">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  <span className="text-slate-400 ml-1">{plan.period}</span>
                </div>
                <p className="text-slate-400 text-sm mb-6">{plan.description}</p>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-center gap-3 text-sm text-slate-300">
                      <span className="text-amber-400 flex-shrink-0">✓</span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <button
                  className={`w-full py-3 rounded-xl font-semibold transition-all duration-200 ${
                    plan.highlighted
                      ? "bg-amber-500 hover:bg-amber-400 text-slate-900"
                      : "border border-slate-600 hover:border-amber-500 text-slate-300 hover:text-white"
                  }`}
                >
                  {plan.cta}
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-amber-500/10 to-amber-600/10 border-t border-amber-500/20 py-20 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Get Your Free Export Health Check
          </h2>
          <p className="text-xl text-slate-400 mb-8">
            Find out exactly how much you're leaving on the table. Takes 30 seconds.
            AI-generated, company-specific report.
          </p>
          <a
            href="#hero"
            className="inline-block bg-amber-500 hover:bg-amber-400 text-slate-900 font-bold px-10 py-4 rounded-xl text-lg transition-all duration-200 hover:shadow-lg hover:shadow-amber-500/25"
          >
            Start Free — No Card Needed
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 border-t border-slate-800 py-12 px-4">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div>
            <span className="text-amber-400 font-bold text-xl">TradingIntel</span>
            <p className="text-slate-500 text-sm mt-1">
              AI-Powered Trade Intelligence for Indian Exporters
            </p>
          </div>
          <div className="flex gap-8 text-slate-500 text-sm">
            <a href="/dashboard" className="hover:text-white transition-colors">Dashboard</a>
            <a href="#pricing" className="hover:text-white transition-colors">Pricing</a>
            <a href="mailto:hello@tradingintel.in" className="hover:text-white transition-colors">Contact</a>
          </div>
          <p className="text-slate-600 text-sm">© 2026 TradingIntel. All rights reserved.</p>
        </div>
      </footer>
    </>
  );
}

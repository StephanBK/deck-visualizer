// The service lineup shown on the home screen. Exactly one is live today;
// the rest are showcased as coming soon (tap -> pitch sheet) to gauge
// customer and rep interest before we build them.
export const SERVICES = [
  {
    id: "deck",
    icon: "🪵",
    name: "Deck",
    tagline: "Resurface, rebuild, or add a brand-new deck",
    available: true,
  },
  {
    id: "kitchen",
    icon: "🍳",
    name: "Kitchen remodel",
    tagline: "New cabinets, counters & layout",
    available: false,
    pitch: {
      headline: "Show the new kitchen before demo day.",
      points: [
        "Photograph the kitchen, pick cabinet fronts, counters, and hardware",
        "Before/after renders of the customer's actual kitchen — not a showroom",
        "Compare door styles and counter materials side by side",
      ],
    },
  },
  {
    id: "bathroom",
    icon: "🛁",
    name: "Bathroom remodel",
    tagline: "Tile, vanities & fixtures",
    available: false,
    pitch: {
      headline: "A new bathroom, rendered in the driveway.",
      points: [
        "Swap tile, vanity, tub-to-shower conversions on the customer's photo",
        "Compare tile patterns and finishes instantly",
        "Same before/after slider and shareable renders as the deck tool",
      ],
    },
  },
  {
    id: "garden",
    icon: "🌿",
    name: "Garden & landscaping",
    tagline: "Patios, plantings & outdoor living",
    available: false,
    pitch: {
      headline: "The whole backyard, reimagined.",
      points: [
        "Patios, walkways, planting beds, lighting and fencing concepts",
        "Pairs naturally with a new deck render for a full outdoor pitch",
        "Declutter + staging, just like the deck visualizer",
      ],
    },
  },
];

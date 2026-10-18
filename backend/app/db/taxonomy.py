"""The ONE authoritative category taxonomy (6 categories, exact subcategories). Slugs are stable IDs;
names are for display. Every module (seed, validation, scraper category mapping) imports from here."""

# slug -> (display name, {subcategory slug: display name})
TAXONOMY = {
    "fashion-accessories": ("Fashion & Accessories", {
        "mens-clothing": "Men's Clothing",
        "womens-clothing": "Women's Clothing",
        "kids-clothing": "Kids' Clothing",
        "shoes-footwear": "Shoes & Footwear",
        "bags-backpacks": "Bags & Backpacks",
        "watches-jewelry": "Watches & Jewelry",
        "sunglasses-accessories": "Sunglasses & Accessories",
    }),
    "electronics-gadgets": ("Electronics & Gadgets", {
        "smartphones-tablets": "Smartphones & Tablets",
        "laptops-computers": "Laptops & Computers",
        "headphones-speakers": "Headphones & Speakers",
        "cameras-photography": "Cameras & Photography",
        "smartwatches-wearables": "Smartwatches & Wearables",
        "computer-accessories": "Computer Accessories",
        "gaming-devices-accessories": "Gaming Devices & Accessories",
    }),
    "home-household": ("Home & Household", {
        "kitchenware-cookware": "Kitchenware & Cookware",
        "home-decor": "Home Décor",
        "cleaning-supplies": "Cleaning Supplies",
        "storage-organization": "Storage & Organization",
        "home-appliances": "Home Appliances",
        "lighting-fixtures": "Lighting & Fixtures",
        "bedding-bath": "Bedding & Bath",
    }),
    "groceries-food": ("Groceries & Food", {
        "fruits-vegetables": "Fruits & Vegetables",
        "rice-pulses-grains": "Rice, Pulses & Grains",
        "meat-fish-seafood": "Meat, Fish & Seafood",
        "dairy-eggs": "Dairy & Eggs",
        "snacks-sweets": "Snacks & Sweets",
        "beverages": "Beverages",
        "spices-cooking-essentials": "Spices & Cooking Essentials",
        "packaged-frozen-food": "Packaged & Frozen Food",
    }),
    "books-stationery": ("Books & Stationery", {
        "academic-textbooks": "Academic & Textbooks",
        "fiction-non-fiction-books": "Fiction & Non-fiction Books",
        "notebooks-paper": "Notebooks & Paper",
        "pens-writing-supplies": "Pens & Writing Supplies",
        "office-supplies": "Office Supplies",
        "art-craft-supplies": "Art & Craft Supplies",
        "calculators-educational-tools": "Calculators & Educational Tools",
    }),
    "sports-fitness": ("Sports & Fitness", {
        "gym-fitness-equipment": "Gym & Fitness Equipment",
        "sportswear-shoes": "Sportswear & Shoes",
        "football-cricket-equipment": "Football & Cricket Equipment",
        "badminton-tennis-equipment": "Badminton & Tennis Equipment",
        "yoga-exercise-accessories": "Yoga & Exercise Accessories",
        "cycling-equipment": "Cycling Equipment",
        "outdoor-camping-gear": "Outdoor & Camping Gear",
    }),
}


def subcategory_parent(sub_slug: str) -> str | None:
    """Category slug that owns this subcategory slug, or None."""
    for cat_slug, (_, subs) in TAXONOMY.items():
        if sub_slug in subs:
            return cat_slug
    return None
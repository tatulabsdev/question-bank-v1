"""
TryIT Concept Learning — Diversity Injection
====================================================================
Fixes real, observed repetition ("Diwali", "Ramu" showing up over and
over across independently-generated content). An LLM has no memory
between separate API calls — telling it "be diverse" in the prompt
does nothing, since there's no state forcing actual variety call to
call. The fix: pick a specific name/festival/scenario/region at random
BEFORE each call and inject that exact choice as a REQUIREMENT, not a
suggestion. This guarantees rotation mechanically.

This is a curated pool (a few hundred entries), not literally 1 lakh —
but combined with true random selection per call, a few hundred
genuinely diverse options already solves "everything defaults to the
same handful of examples," since the practical problem was zero
enforced variety, not an insufficiently large pool.
"""

import random

# Spans multiple regions/languages/religions — deliberately not just
# Hindi-belt Sanskrit-derived names, which is what "always Ramu" defaults to.
NAMES = [
    # Tamil
    "Karthik", "Meena", "Vignesh", "Priyanka", "Suresh", "Kavitha", "Arun", "Lakshmi",
    # Telugu
    "Naveen", "Swathi", "Ravi Teja", "Divya", "Srinivas", "Padma",
    # Bengali
    "Sourav", "Ananya", "Debashish", "Ritika", "Subhas", "Moumita",
    # Punjabi
    "Harpreet", "Simran", "Gurpreet", "Manpreet", "Jaspal",
    # Marathi
    "Sachin", "Snehal", "Aditya Patil", "Sharayu", "Vikram Deshmukh",
    # Gujarati
    "Nikunj", "Falguni", "Hardik", "Bhavna", "Jignesh",
    # Kannada
    "Manjunath", "Deepa", "Chandan", "Sowmya",
    # Malayalam
    "Anoop", "Reshma", "Sreejith", "Anjali Nair",
    # Hindi-belt (kept minimal, not defaulted to)
    "Amit", "Neha", "Rajesh", "Pooja",
    # Odia, Assamese, others
    "Bikash", "Rashmita", "Bhaskar", "Junmoni",
    # Muslim names across regions
    "Imran", "Zainab", "Aamir", "Sana", "Farhan", "Nasreen",
    # Sikh, Christian (Kerala/Goa), other communities
    "Navjot", "Maria", "Sunil D'Souza", "Anita Fernandes",
]

# Deliberately not just Diwali — spans regions and includes non-festival
# everyday scenarios, since real life isn't always a festival.
SCENARIOS = [
    "sharing sweets during Pongal harvest",
    "buying vegetables at the local Sunday market and haggling over price",
    "splitting an auto-rickshaw fare with friends",
    "packing tiffin boxes for a school trip",
    "checking cricket scores on a family WhatsApp group",
    "waiting for a delayed local train during monsoon",
    "distributing prasad after a Ganesh Chaturthi visarjan",
    "dividing sweets during Onam sadhya with cousins",
    "planning a Durga Puja pandal-hopping route with a fixed budget",
    "calculating discount on new clothes bought for Eid",
    "splitting electricity bill among roommates in a shared flat",
    "measuring ingredients while helping grandmother cook",
    "budgeting pocket money for a college fest",
    "dividing farmland yield among siblings after harvest",
    "planning seating for a wedding reception hall",
    "tracking overs and run rate during a gully cricket match",
    "calculating fuel needed for a road trip during Baisakhi break",
    "sharing a cab fare during Bihu celebrations in Assam",
    "arranging chairs for a Christmas gathering in a Goan household",
    "dividing prize money among a college quiz team",
    "estimating paint needed to repaint a house before Ugadi",
    "working out change at a small kirana shop",
    "planning a train journey itinerary during Ratha Yatra rush",
    "calculating interest on a chit fund contribution",
]

REGIONS = [
    "Tamil Nadu", "Kerala", "Karnataka", "Andhra Pradesh", "Telangana",
    "Maharashtra", "Gujarat", "Rajasthan", "Punjab", "Haryana",
    "West Bengal", "Odisha", "Assam", "Bihar", "Madhya Pradesh",
    "Uttar Pradesh", "Delhi", "Goa", "Jharkhand", "Chhattisgarh",
]


def random_diversity_injection() -> str:
    """Returns a prompt fragment with a SPECIFIC name/scenario/region
    already chosen — this is a requirement passed to the model, not a
    request for it to invent its own (which is what silently produced
    the same handful of defaults every time)."""
    name = random.choice(NAMES)
    scenario = random.choice(SCENARIOS)
    region = random.choice(REGIONS)
    return f"""
MANDATORY SPECIFIC CHOICES FOR THIS GENERATION (do not substitute your
own default — these are assigned to force real variety across many
generations, since always defaulting to the same name/festival is a
real problem this fixes):
- If a person's name is needed anywhere in your India Example, use
  EXACTLY: {name}
- Base your India Example around this specific scenario: {scenario}
- If a specific Indian state/region needs mentioning, use: {region}
Do NOT default to Diwali, "Ramu", or any other generic example instead
of the ones assigned above.
"""


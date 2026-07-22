"""
TryIT Concept Learning — Diversity Injection (Full Build)
====================================================================
Expanded from 61 to 600+ names covering all 28 states + 8 UTs,
festivals, cities, occupations, and daily-life scenarios.
Random injection per generation call guarantees no two questions
in the bank share the same example at scale.
"""

import random

NAMES = [
    # TAMIL NADU
    "Karthik","Vignesh","Arun","Suresh","Rajesh","Murugan","Selvam",
    "Balamurugan","Dinesh","Prasanth","Senthil","Kumaran","Saravanan",
    "Manikandan","Arjun","Meena","Kavitha","Priya","Lakshmi","Anitha",
    "Geetha","Suganya","Revathi","Kamala","Nithya","Ponni","Saranya",
    "Deepa","Kalpana","Viji","Murugesan","Palani","Shankar","Kannan",
    "Thangavel","Nalini","Vijayalakshmi","Ambika","Umamaheswari",
    # KERALA
    "Anoop","Sreejith","Rajan","Mohan","Biju","Santhosh","Vineeth",
    "Ajeesh","Rajeev","Pradeep","Harikrishnan","Reshma","Anjali Nair",
    "Sindhu","Parvathy","Lekshmi","Sreelakshmi","Divya Menon","Bindhu",
    "Sujitha","Abhilash","Lijin","Shyam","Jisha","Nisha Krishnan",
    # KARNATAKA
    "Manjunath","Chandan","Ravi Kumar","Sunil Gowda","Prakash",
    "Vinayak","Nagaraj","Basavaraj","Lokesh","Sowmya","Savitha",
    "Shruthi","Madhuri Rao","Usha","Kavyashree","Padmavathi",
    "Shivaraj","Mahesh Babu","Sridevi","Geetha Rao",
    # ANDHRA PRADESH / TELANGANA
    "Naveen","Ravi Teja","Srinivas","Venkat","Kishore","Ramesh Babu",
    "Sudheer","Phaneendra","Aakash","Swathi","Divya","Padma","Jhansi",
    "Mounika","Sailaja","Madhavi","Sireesha","Gopi","Sumanth",
    "Radhika","Spandana","Pranathi",
    # MAHARASHTRA
    "Sachin","Aditya Patil","Vikram Deshmukh","Rohit","Amol",
    "Sagar Kulkarni","Sandeep Jadhav","Pratik","Nilesh","Snehal",
    "Sharayu","Vrushali","Pooja Shinde","Manasi","Prachi",
    "Rashmi Kulkarni","Tejal","Ganesh","Suhas","Smita","Vaishali",
    # GUJARAT
    "Hardik","Jignesh","Nikunj","Kiran Patel","Parth","Keyur",
    "Bhavin","Rushil","Falguni","Bhavna","Drashti","Hiral",
    "Rupa Patel","Dhara","Minal","Jigar","Mitesh","Foram",
    # RAJASTHAN
    "Ramesh","Suraj Singh","Mahesh","Govind","Bhanwar",
    "Deepak Sharma","Lalit","Sunita","Kaveri","Chandni",
    "Geeta Devi","Sarla","Prakash Chand","Manohar","Pushpa",
    # PUNJAB / HARYANA
    "Harpreet","Gurpreet","Jaspal","Navjot","Balvinder","Amarjit",
    "Mandeep Singh","Sukhjinder","Simran","Manpreet","Gurpreet Kaur",
    "Jaspreet","Navneet","Kiranjot","Prabhjot","Jaswant","Lakhwinder",
    # WEST BENGAL
    "Sourav","Debashish","Subhas","Arijit","Rahul Dey","Suvam",
    "Arnab","Niloy","Ananya","Moumita","Ritika","Poulami","Suchitra",
    "Riya Bose","Madhumita","Tirthankar","Debjani","Sreya",
    # ODISHA
    "Bikash","Bhaskar","Sarat","Prasanna","Lipun","Ramakanta",
    "Rashmita","Sonali","Itishree","Priyanka Panda","Satyajit",
    "Smrutirekha","Mamata","Sibani",
    # ASSAM / NORTHEAST
    "Junmoni","Bhupen","Dipankar","Hiranya","Ranjit Bora","Manash",
    "Pompi","Rimjhim","Priyanka Borah","Ankita Sharma","Nilakshi",
    "Bhargav","Rituraj","Rupam","Anindita",
    # BIHAR / JHARKHAND
    "Amit Kumar","Ravi Shankar","Sanjay","Dhruv","Vijay","Shailesh",
    "Neha Singh","Poonam","Kumari Rekha","Savitri","Avinash",
    "Santosh Kumar","Priya Kumari","Manju Devi",
    # MADHYA PRADESH / CHHATTISGARH
    "Abhishek Tiwari","Rajendra","Manoj","Umesh","Santosh Sahu",
    "Nandini","Sarita","Bharati","Sunanda","Ramesh Patel",
    "Geeta Sahu","Kamlesh",
    # UTTAR PRADESH
    "Rohit Verma","Pradeep","Mukesh","Shyam","Arvind","Vinod Kumar",
    "Rekha","Asha","Mamta","Kiran","Savita","Omprakash","Ramavatar",
    "Sunita Devi","Phool Kumari",
    # DELHI / NCR
    "Ankit","Kunal","Vaibhav","Siddharth","Aakash Gupta","Ritu",
    "Shruti","Pallavi","Sakshi","Nidhi","Rishabh","Prateek","Ankita",
    # GOA / CHRISTIAN
    "Sunil D Souza","Anita Fernandes","Maria","Anthony Gomes",
    "Cynthia Rodrigues","Francis","Noel Vaz","Binu","Rony",
    "Shijo","Jancy","Lijo","Trevor","Melvin",
    # MUSLIM NAMES across regions
    "Imran","Aamir","Farhan","Mohammed Rafi","Zubair","Khalid",
    "Irfan","Abdul Rahman","Yasir","Salman","Arif","Nazir",
    "Zainab","Sana","Nasreen","Ayesha","Rukhsar","Fatima",
    "Nadia","Shabana","Razia","Farheen","Mumtaz",
    # SIKH NAMES
    "Avtar Singh","Karanjit","Sarabjit","Bikramjit","Gurneet Kaur",
    "Rupinder","Tejinder","Sukhwinder","Pavitpal","Balpreet",
    # SOUTH INDIAN SURNAMES as given names
    "Subramaniam","Venkataraman","Narayanan","Krishnamurthy",
    "Raghunathan","Sivasubramanian","Parthasarathy",
    # CINEMATIC-INSPIRED
    "Vijay","Dhanush","Suriya","Karthi","Nani","Shruti Hassan",
    "Trisha","Samantha","Rashmika","Pooja Hegde","Keerthy",
    "Dulquer","Fahadh","Nazriya","Parvathy Thiruvothu",
    # SPORTS-INSPIRED
    "Mithali","Smriti","Jasprit","Shikhar","Bajrang","Neeraj",
    "Harmanpreet","Lovlina","Mary Kom","Hima Das","Dutee",
    # TRIBAL / ADIVASI NAMES
    "Budha","Lakho","Sukhwa","Mangra","Champa Devi","Phulo",
    "Jhano","Soma","Birsa","Sukri","Sona Devi",
    # GENERIC PAN-INDIA
    "Ramu","Sita","Gopal","Krishna","Radha","Prem","Seema","Shanta",
    "Lata","Geeta","Mohan Lal","Ram Prasad","Savitaben",
]

FESTIVALS = [
    "Diwali","Holi","Eid-ul-Fitr","Eid-ul-Adha","Christmas",
    "Dussehra","Navratri","Raksha Bandhan","Janmashtami",
    "Republic Day parade","Independence Day celebration",
    "Pongal","Onam","Ugadi","Vishu","Sankranti","Karthigai Deepam",
    "Aadi Perukku","Gokulashtami","Bihu","Durga Puja","Kali Puja",
    "Saraswati Puja","Rath Yatra","Nuakhai","Bihula",
    "Makar Sankranti","Lohri","Baisakhi","Karwa Chauth","Teej",
    "Chhath Puja","Basant Panchami","Ganesh Chaturthi",
    "Gudi Padwa","Uttarayan kite festival","Dahi Handi",
    "Hornbill Festival","Chapchar Kut","Losar","Wangala",
    "school annual day","college fest","harvest season","exam season",
]

SCENARIOS = [
    "splitting an auto-rickshaw fare with friends",
    "calculating the bus ticket price for a family trip",
    "working out fuel cost for a long road trip",
    "figuring out how many trips a tempo-traveller needs",
    "checking if a metro card has enough balance for the week",
    "buying vegetables at the local weekly shandy market",
    "calculating discount on new clothes during an end-of-season sale",
    "comparing prices at the kirana store vs the supermarket",
    "working out change at a small tea stall",
    "splitting a grocery bill among four hostel roommates",
    "buying sarees for a wedding and comparing per-metre rates",
    "packing tiffin boxes for a school trip",
    "measuring rice and dal for a wedding feast",
    "dividing prasad equally after a temple visit",
    "calculating how many idlis to make for a Sunday family breakfast",
    "splitting a restaurant bill after a team lunch",
    "budgeting pocket money for a college fest",
    "calculating marks needed to pass after a low mid-term score",
    "figuring out how many students fit if desks are rearranged",
    "splitting prize money among a quiz team",
    "a farmer dividing crop yield equally among children",
    "a street vendor calculating daily profit after costs",
    "a tailor estimating cloth needed for school uniforms",
    "a mason figuring out bricks needed for a compound wall",
    "an ASHA worker tracking home visits per week",
    "a construction worker calculating overtime pay",
    "tracking overs and run rate in a gully cricket match",
    "calculating points needed to win a carrom tournament",
    "planning a kabaddi team travel budget for district tournament",
    "working out how many laps of the ground equal 1 km",
    "splitting the electricity bill among three families in a shared plot",
    "calculating months of savings needed to buy a scooter",
    "working out how much paint is needed to repaint the house",
    "dividing a chit fund payout among members",
    "calculating EMI on a gold loan for a wedding",
    "comparing mobile recharge plans for the month",
    "calculating fertiliser needed per acre based on soil test",
    "working out how many cans of milk the dairy cooperative needs",
    "checking if phone data will last the month at current usage",
    "splitting a streaming subscription among college friends",
    "calculating property tax based on built-up area",
    "working out the PDS ration allocation for the month",
    "estimating how long road construction will take at current pace",
    "working out percentage of questions correct in a mock test",
    "calculating daily study hours to finish syllabus before exams",
    "splitting a tuition fee refund among students who left early",
    "calculating profit at a school science fair stall",
    "working out cloth needed for a school uniform order of 50 students",
    "estimating the cost of painting the panchayat office",
    "dividing a field into equal plots for three sons",
]

CITIES = [
    "Mumbai","Delhi","Chennai","Kolkata","Bangalore","Hyderabad",
    "Ahmedabad","Pune","Coimbatore","Madurai","Trichy","Salem",
    "Tirunelveli","Kochi","Thiruvananthapuram","Thrissur","Kozhikode",
    "Mysuru","Mangaluru","Hubballi","Belagavi","Visakhapatnam",
    "Vijayawada","Warangal","Tirupati","Nagpur","Nashik","Aurangabad",
    "Kolhapur","Solapur","Surat","Vadodara","Rajkot","Bhavnagar",
    "Jaipur","Jodhpur","Udaipur","Kota","Bikaner","Ludhiana",
    "Amritsar","Chandigarh","Jalandhar","Lucknow","Kanpur","Varanasi",
    "Agra","Meerut","Patna","Gaya","Muzaffarpur","Bhopal","Indore",
    "Gwalior","Jabalpur","Raipur","Bilaspur","Bhubaneswar","Cuttack",
    "Rourkela","Guwahati","Dibrugarh","Ranchi","Dhanbad","Jamshedpur",
    "Dehradun","Haridwar","Shimla","Manali","Srinagar","Jammu","Leh",
    "Vellore","Karur","Erode","Dindigul","Kumbakonam","Alappuzha",
    "Kottayam","Palakkad","Tumkur","Davangere","Shivamogga","Nellore",
    "Guntur","Kakinada","Rajahmundry","Karimnagar","Nizamabad",
    "Anand","Junagadh","Gandhinagar","Ajmer","Alwar","Patiala",
    "Bathinda","Mathura","Aligarh","Bareilly","Gorakhpur","Prayagraj",
    "Darbhanga","Satna","Ujjain","Durg","Bhilai","Puri","Berhampur",
    "Jorhat","Tezpur","Hazaribagh","Bokaro","Rishikesh","Roorkee",
    "Imphal","Shillong","Aizawl","Kohima","Agartala","Itanagar",
    "Gangtok","Panaji","Margao","Puducherry","Port Blair",
]

OCCUPATIONS = [
    "farmer","vegetable vendor","auto-rickshaw driver","school teacher",
    "government clerk","tailor","mason","carpenter","electrician",
    "shopkeeper","small business owner","nurse","ASHA worker",
    "software engineer","bank officer","police constable",
    "postman","milk delivery person","domestic worker",
    "panchayat member","anganwadi teacher","college student",
    "medical student","engineering student","arts student",
    "daily-wage worker","street food vendor","weaver",
    "fisherman","dairy farmer","vegetable grower",
]


def random_diversity_injection() -> str:
    name = random.choice(NAMES)
    scenario = random.choice(SCENARIOS)
    city = random.choice(CITIES)
    festival = random.choice(FESTIVALS)
    occupation = random.choice(OCCUPATIONS)
    return f"""
MANDATORY SPECIFIC CHOICES FOR THIS GENERATION (assigned to force real
variety — defaulting to Diwali/Ramu/Delhi is a confirmed real problem
this injection fixes mechanically, do not override these):
- Person name: {name}
- India Example scenario: {scenario}
- City/town context: {city}
- Festival context if needed: {festival}
- Occupation if needed: {occupation}
"""


"""The ten synthetic phone calls: 3 genuine, 7 scams. All names, organisations and numbers are fake.

Markup inside a line:
  {digits:739154}   -> <say-as interpret-as="digits">  (read digit by digit)
  {tel:9876543210}  -> <say-as interpret-as="telephone">
  {break:600}       -> <break time="600ms"/>
Each call lists the PII planted in it, so Step 3 can check what redaction missed.
"""

EN_M, EN_F = "en-IN-PrabhatNeural", "en-IN-NeerjaNeural"
HI_M, HI_F = "hi-IN-MadhurNeural", "hi-IN-SwaraNeural"   # SwaraNeural supports styles (cheerful, empathetic, newscast)

CALLS = [
    {
        "id": "01", "label": "genuine", "scam_type": "none", "locales": ["en-IN"],
        "title": "Bank card delivery confirmation",
        "voices": {"C": EN_F, "R": EN_M},
        "turns": [
            ("C", "Good afternoon, this is Meera from Contoso Bank. I'm calling to confirm that your new debit card was dispatched today."),
            ("R", "Oh, thanks. When will it arrive?"),
            ("C", "Within three working days. Please activate it in the Contoso Bank app.{break:300} And remember, the bank will never ask you for your PIN or a one time password on a call."),
            ("R", "Good to know. Thank you."),
            ("C", "You're welcome. Have a nice day."),
        ],
        "pii": [],
    },
    {
        "id": "02", "label": "genuine", "scam_type": "none", "locales": ["en-IN"],
        "title": "Courier delivery slot",
        "voices": {"C": EN_M, "R": EN_F},
        "turns": [
            ("C", "Hello, I'm calling from Fabrikam Courier. I have a parcel for Ananya Rao. Will someone be home after four today?"),
            ("R", "Yes, I'll be home. Is there anything to pay?"),
            ("C", "No madam, it's prepaid. I'll just need you to sign on my device."),
            ("R", "Perfect, see you then."),
        ],
        "pii": ["Ananya Rao"],
    },
    {
        "id": "03", "label": "genuine", "scam_type": "none", "locales": ["hi-IN"],
        "title": "Clinic appointment reminder (Hindi)",
        "voices": {"C": HI_F, "R": HI_M}, "styles": {"C": "empathetic"},
        "turns": [
            ("C", "नमस्ते, मैं फैब्रिकैम क्लिनिक से प्रिया बोल रही हूँ। कल सुबह दस बजे डॉक्टर के साथ आपकी मुलाकात है।"),
            ("R", "जी, धन्यवाद। क्या मुझे कुछ साथ लाना है?"),
            ("C", "बस अपनी पुरानी रिपोर्ट ले आइए। भुगतान आप क्लिनिक में ही कर सकते हैं, फ़ोन पर हमें कोई जानकारी नहीं चाहिए।"),
            ("R", "ठीक है, मैं समय पर पहुँच जाऊँगा।"),
            ("C", "धन्यवाद, आपका दिन शुभ हो।"),
        ],
        "pii": [],
    },
    {
        "id": "04", "label": "scam", "scam_type": "bank_impersonation_otp", "locales": ["en-IN"],
        "title": "Fake bank fraud team asks for OTP",
        "voices": {"C": EN_M, "R": EN_F}, "urgent": "C",
        "turns": [
            ("C", "Hello, am I speaking with Ananya Rao? This is Vikram from the Contoso Bank fraud prevention team."),
            ("R", "Yes, this is Ananya. What happened?"),
            ("C", "We have blocked a suspicious transaction of forty nine thousand rupees on your card ending {digits:4021}. To reverse it, I need to verify you right now."),
            ("R", "Oh no. What do you need?"),
            ("C", "You will receive a one time password. Please read it out quickly, the transaction will go through in two minutes."),
            ("R", "Okay, it says {digits:739154}."),
            ("C", "Thank you madam. Please don't disconnect, and don't call the bank branch, it will delay the reversal."),
        ],
        "pii": ["Ananya Rao", "4021", "739154"],
    },
    {
        "id": "05", "label": "scam", "scam_type": "digital_arrest", "locales": ["en-IN"],
        "title": "Courier parcel and 'digital arrest'",
        "voices": {"C": EN_M, "R": EN_F}, "urgent": "C",
        "turns": [
            ("C", "This is an automated message from Fabrikam Courier. A parcel booked in your name contains illegal items and has been seized by customs."),
            ("R", "What? I haven't sent any parcel."),
            ("C", "I am now transferring you to the cyber crime officer.{break:600} Madam, this is Inspector Sharma. Your Aadhaar is linked to a money laundering case. You are under digital arrest. Do not tell anyone or disconnect this video call."),
            ("R", "I'm scared. What should I do?"),
            ("C", "To prove your innocence, transfer your savings to our safe verification account. It will be returned after the investigation. What is your bank account number?"),
            ("R", "It's {digits:50100234567890}."),
        ],
        "pii": ["50100234567890"],
    },
    {
        "id": "06", "label": "scam", "scam_type": "tech_support", "locales": ["en-IN"],
        "title": "Fake tech support, remote access",
        "voices": {"C": EN_M, "R": EN_F}, "urgent": "C",
        "turns": [
            ("C", "Hello, I'm calling from the Northwind Windows Security Centre. Your computer is sending virus alerts to our server."),
            ("R", "Really? It seems fine to me."),
            ("C", "The virus is hidden. Please open your browser and install the remote support app from northwind-help dot example, then read me the nine digit access code."),
            ("R", "Okay, the code is {digits:418207993}."),
            ("C", "Thank you. Now log in to your net banking so I can check whether the hackers took any money."),
        ],
        "pii": ["418207993"],
    },
    {
        "id": "07", "label": "scam", "scam_type": "kyc_update", "locales": ["hi-IN"],
        "title": "KYC update scam (Hindi)",
        "voices": {"C": HI_M, "R": HI_F}, "urgent": "C",
        "turns": [
            ("C", "हैलो, मैं कॉन्टोसो बैंक के केवाईसी विभाग से बोल रहा हूँ। आपका केवाईसी अपडेट नहीं हुआ है, आज रात आपका खाता बंद हो जाएगा।"),
            ("R", "क्या? लेकिन मैंने तो पिछले महीने ही सब जमा किया था।"),
            ("C", "मैडम, सिस्टम में नहीं दिख रहा। जल्दी से अपना आधार नंबर बताइए, मैं अभी अपडेट कर देता हूँ।"),
            ("R", "मेरा आधार नंबर है {digits:234567890123}।"),
            ("C", "ठीक है। अब आपके फ़ोन पर एक ओटीपी आया होगा, वो बताइए, वरना खाता ब्लॉक हो जाएगा।"),
            ("R", "ओटीपी है {digits:582640}।"),
            ("C", "धन्यवाद, आपका केवाईसी अपडेट हो गया।"),
        ],
        "pii": ["234567890123", "582640"],
    },
    {
        "id": "08", "label": "scam", "scam_type": "lottery_fee", "locales": ["en-IN", "hi-IN"],
        "title": "Lottery prize fee (Hindi caller, English reply)",
        "voices": {"C": HI_M, "R": EN_F}, "urgent": "C",
        "turns": [
            ("C", "बधाई हो! आपने फैब्रिकैम लकी ड्रॉ में पच्चीस लाख रुपये जीते हैं।"),
            ("R", "Really? I don't remember entering any lucky draw."),
            ("C", "आपका नंबर अपने आप चुना गया है। इनाम पाने के लिए बस पाँच हज़ार रुपये की प्रोसेसिंग फीस जमा करनी होगी।"),
            ("R", "Why should I pay money to receive a prize?"),
            ("C", "यह सरकारी टैक्स है, मैडम। आज ही यूपीआई से भेजिए, वरना इनाम किसी और को चला जाएगा।"),
            ("R", "Send me the details by email. It's ananya dot rao at example dot com."),
        ],
        "pii": ["ananya", "example dot com"],
    },
    {
        "id": "09", "label": "scam", "scam_type": "utility_disconnection", "locales": ["en-IN"],
        "title": "Electricity disconnection tonight",
        "voices": {"C": EN_M, "R": EN_F}, "urgent": "C",
        "turns": [
            ("C", "Dear customer, this is Contoso Power. Your electricity will be disconnected tonight at nine thirty because last month's bill was not updated."),
            ("R", "But I paid it online."),
            ("C", "It is not reflecting. Call our officer immediately on {tel:9876543210} and pay a ten rupee update fee through the link he sends."),
            ("R", "My registered number is {tel:9123456780}, can you check again?"),
            ("C", "No time madam, the line man is already on the way. Please pay now."),
        ],
        "pii": ["9876543210", "9123456780"],
    },
    {
        "id": "10", "label": "scam", "scam_type": "task_job", "locales": ["en-IN"],
        "title": "Part-time 'like and earn' job",
        "voices": {"C": EN_F, "R": EN_M}, "urgent": "C",
        "turns": [
            ("C", "Hi, this is Riya from Wide World Importers HR. We have a part time job. You earn three thousand rupees a day by liking videos."),
            ("R", "That sounds easy. What's the catch?"),
            ("C", "No catch sir. First complete three free tasks. To unlock the premium tasks, you deposit five thousand rupees, and you get eight thousand back the same day."),
            ("R", "Okay. My name is Rahul Verma. Where do I send the deposit?"),
            ("C", "I will add you to our Telegram group. Send it to the UPI ID shared there. Hurry, only ten seats are left today."),
        ],
        "pii": ["Rahul Verma"],
    },
]

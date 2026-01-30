// chatbot.js
// ----------------------------
// SMART MALL AI CHATBOT (Text + Voice)
// ----------------------------

// Elements
const messages = document.getElementById("messages");
const chatInput = document.getElementById("chat_input");
const sendBtn = document.getElementById("send");
const speakBtn = document.getElementById("speak");
const langSelect = document.getElementById("langSelect");


let voices = [];

function loadVoices() {
    voices = window.speechSynthesis.getVoices();
}

window.speechSynthesis.onvoiceschanged = loadVoices;


// Detect Kannada text
function isKannada(text) {
    return /[\u0C80-\u0CFF]/.test(text);
}

// Helper: add messages to chat
function appendMessage(sender, text) {
    const div = document.createElement("div");
    div.style.margin = "5px 0";
    div.innerHTML = `<b>${sender}:</b> ${text}`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

// ----------------------------
// CHATBOT CORE LOGIC
// ----------------------------
function chatbotResponse(text) {
    text = text.toLowerCase().trim();
    const q = text;
    // ---------------- KANNADA SUPPORT ----------------

    // Greetings (Kannada)
    if (/(ಹಾಯ್|ನಮಸ್ಕಾರ|ಹಲೋ)/.test(q))
        return "🙏 ನಮಸ್ಕಾರ! ಸ್ಮಾರ್ಟ್ ಮಾಲ್‌ಗೆ ಸ್ವಾಗತ. ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಲಿ?";

    if (q.includes("ಧನ್ಯವಾದ"))
        return "😊 ಧನ್ಯವಾದಗಳು! ಶುಭ ದಿನವಾಗಲಿ.";

    // Mall timing
    if (q.includes("ಸಮಯ") || q.includes("ತೆರೆದಿದೆ"))
        return "🕙 ಮಾಲ್ ಸಮಯ: ಬೆಳಿಗ್ಗೆ 10 ರಿಂದ ರಾತ್ರಿ 10 ರವರೆಗೆ.";

    // Parking
    if (q.includes("ಪಾರ್ಕಿಂಗ್"))
        return "🚗 ಪಾರ್ಕಿಂಗ್ ಸೌಲಭ್ಯ ಬೆಸ್ಮೆಂಟ್‌ನಲ್ಲಿ ಲಭ್ಯವಿದೆ. ಗೇಟ್ 2ರಿಂದ ಪ್ರವೇಶ.";

    // Food court
    if (q.includes("ಆಹಾರ") || q.includes("ಫುಡ್ ಕೋರ್ಟ್"))
        return "🍽️ ಫುಡ್ ಕೋರ್ಟ್ ಲೆವಲ್ 2ರಲ್ಲಿ ಇದೆ.";

    // Washroom
    if (q.includes("ಶೌಚಾಲಯ") || q.includes("ಟಾಯ್ಲೆಟ್"))
        return "🚻 ಶೌಚಾಲಯಗಳು ಎಲ್ಲಾ ಮಹಡಿಗಳಲ್ಲೂ ಲಿಫ್ಟ್ ಹತ್ತಿರ ಲಭ್ಯವಿವೆ.";

    // Lift
    if (q.includes("ಲಿಫ್ಟ್") || q.includes("ಎಲಿವೇಟರ್"))
        return "⬆️⬇️ ಲಿಫ್ಟ್‌ಗಳು ಪ್ರತಿಯೊಂದು ಮಹಡಿಯ ಮಧ್ಯಭಾಗದಲ್ಲಿ ಇವೆ.";

    // Exit
    if (q.includes("ನಿರ್ಗಮನ") || q.includes("ಬಿಟ್ಟು ಹೋಗುವ"))
        return "🚪 ಮುಖ್ಯ ನಿರ್ಗಮನ ದ್ವಾರ ಗ್ರೌಂಡ್ ಫ್ಲೋರ್‌ನಲ್ಲಿ ಇದೆ.";



    // Greetings
    if (/(^|\b)(hi|hello|hey|good morning|good evening)\b/.test(text))
        return "👋 Hello! Welcome to the Smart Mall. How can I help you today?";
    if (text.includes("thank")) return "😊 You’re welcome! Enjoy your visit.";

    // Facilities
    if (q.includes('atm') || q.includes('cash'))
        return "There are ATMs near the main entrance beside the information desk.";
    if (q.includes('elevator') || q.includes('lift'))
        return "Elevators are located at the center of every floor.";
    if (q.includes('escalator'))
        return "Escalators are available on the east and west ends of each floor.";
    if (q.includes('exit'))
        return "The main exit is on the ground floor near the reception area.";
    if (q.includes('entrance'))
        return "There are two entrances: North Gate and South Gate.";
    if (q.includes('stairs') || q.includes('step'))
        return "Stairs are next to the elevators on all floors.";
    if (q.includes('kids zone') || q.includes('play area'))
        return "Kids Zone is on Level 3 beside the cinema hall.";
    if (q.includes('gaming') || q.includes('game zone'))
        return "Game Zone is located beside the food court on Level 2.";
    if (q.includes('cinema') || q.includes('movie'))
        return "The cinema hall is on Level 3. You can buy tickets at the counter or online.";

    // Mall Information
    if (q.includes('timing') || q.includes('hours') || q.includes('open'))
        return "Mall timings are 10:00 AM to 10:00 PM.";
    if (q.includes('wifi') || q.includes('internet'))
        return "Yes, Free WiFi is available. Connect to 'MallFreeWiFi' and enter your phone number.";
    if (q.includes('security') || q.includes('lost') || q.includes('help desk'))
        return "Security help desk is near Gate 1. You can report any help needed there.";
    if (q.includes('first aid') || q.includes('medical') || q.includes('doctor'))
        return "First Aid Room is located beside the information counter on Ground Floor.";

    // Shops
    if (q.includes('clothes') || q.includes('fashion'))
        return "Fashion stores are mostly on Level 1. You can find Zudio, H&M, Lifestyle and more.";
    if (q.includes('electronics') || q.includes('mobile') || q.includes('laptop'))
        return "Electronic stores like Croma and Reliance Digital are on Level 1.";
    if (q.includes('grocery') || q.includes('supermarket'))
        return "The supermarket is on the basement floor near the parking area.";
    if (q.includes('jewellery') || q.includes('gold'))
        return "Jewelry stores like Tanishq and Kalyan Jewelers are on Level 1.";

    // Offers & Events
    if (q.includes('offer') || q.includes('discount') || q.includes('sale'))
        return "Today's offers: 10% off at Fashion Hub, Buy 1 Get 1 at Sweet Treats.";
    if (q.includes('event') || q.includes('show') || q.includes('live'))
        return "There is a live musical event today at 6 PM near the central atrium.";

    // Food
    if (q.includes('food court'))
        return "The food court is on Level 2 near the south entrance.";
    if (q.includes('pizza'))
        return "You can get pizza at Domino's and Pizza Hut in the food court.";
    if (q.includes('ice cream') || q.includes('dessert'))
        return "Amul and Baskin Robbins are in the food court.";
    if (q.includes('coffee'))
        return "CCD and Starbucks are located on Level 1 beside the escalator.";
    if (q.includes('burger'))
        return "McDonald's and Burger King are in the food court.";
    if (q.includes('restaurant'))
        return "There are multiple restaurants on Level 2 in the food court area.";

    // Services
    if (q.includes('parking'))
        return "Parking is available in the basement. Entry from Gate 2.";
    if (q.includes('wheelchair'))
        return "Wheelchairs are available at the help desk near Gate 1.";
    if (q.includes('baby') || q.includes('stroller'))
        return "Baby strollers can be borrowed at the customer service counter.";
    if (q.includes('charging') || q.includes('charger'))
        return "Charging stations are available near the seating lounges on each floor.";
    if (q.includes('locker') || q.includes('storage'))
        return "Lockers are available on the basement floor near the parking entry.";

    // General
    if (q.includes('who are you') || q.includes('your name'))
        return "I am Mall Assistant Bot, your virtual guide!";

    // Default
    return "Sorry, I don't have that information. Try asking about parking, food court, offers, restrooms, cinema, or events!";
}

// ----------------------------
// EVENT HANDLERS
// ----------------------------

// Text send
sendBtn.addEventListener("click", () => {
    const text = chatInput.value.trim();
    if (!text) return;
    appendMessage("You", text);
    const reply = chatbotResponse(text);
    appendMessage("Bot", reply);
    speak(reply);
    chatInput.value = "";
});

// Press Enter to send
chatInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendBtn.click();
});

// ----------------------------
// VOICE INPUT & OUTPUT
// ----------------------------
let recognition;

if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRec();

    recognition.continuous = false;
    recognition.interimResults = false;

    speakBtn.addEventListener("click", () => {
        try {
            // ✅ Set language based on user selection
            recognition.lang = langSelect.value;
            recognition.start();
        } catch (e) {
            alert("🎤 Mic already in use. Please wait.");
        }
    });

    recognition.onresult = (event) => {
        const speech = event.results[0][0].transcript;

        appendMessage("You (voice)", speech);

        const reply = chatbotResponse(speech);
        appendMessage("Bot", reply);

        // 🔊 Speak ONLY if English selected
        if (langSelect.value === "en-IN") {
            speak(reply);
        }
    };

    recognition.onerror = (event) => {
        alert("🎤 Voice error: " + event.error);
    };

} else {
    speakBtn.disabled = true;
    speakBtn.title = "Speech recognition not supported";
}

// Voice output
function isKannada(text) {
    return /[\u0C80-\u0CFF]/.test(text);
}

function speak(text) {
    if (!text) return;

    const utter = new SpeechSynthesisUtterance(text);

    // Always use English-India voice
    const englishVoice = voices.find(v => v.lang === "en-IN");

    if (englishVoice) {
        utter.voice = englishVoice;
    }

    utter.lang = "en-IN"; // force voice
    utter.rate = 1;
    utter.pitch = 1;

    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utter);
}
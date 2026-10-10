"""Localized error messages for every reason code (en / hi / mr).

Each message tells the health worker what happened and what to do next.
Pending review by native-speaking reviewers before release (PRD §7).
"""

ERROR_MESSAGES: dict[str, dict[str, str]] = {
    "FILE_TOO_LARGE": {
        "en": "This file is too large. Send a smaller file or fewer pages.",
        "hi": "यह फ़ाइल बहुत बड़ी है। छोटी फ़ाइल या कम पेज भेजें।",
        "mr": "ही फाइल खूप मोठी आहे. लहान फाइल किंवा कमी पाने पाठवा.",
    },
    "UNSUPPORTED_TYPE": {
        "en": "This file type is not supported. Send a photo (JPG, PNG, HEIC), a PDF, or a DICOM scan.",
        "hi": "यह फ़ाइल प्रकार समर्थित नहीं है। फ़ोटो (JPG, PNG, HEIC), PDF या DICOM स्कैन भेजें।",
        "mr": "हा फाइल प्रकार चालत नाही. फोटो (JPG, PNG, HEIC), PDF किंवा DICOM स्कॅन पाठवा.",
    },
    "TYPE_MISMATCH": {
        "en": "The file's contents do not match its name or type. Check that you picked the right file.",
        "hi": "फ़ाइल की सामग्री उसके नाम या प्रकार से मेल नहीं खाती। जांचें कि आपने सही फ़ाइल चुनी है।",
        "mr": "फाइलमधील मजकूर तिच्या नावाशी किंवा प्रकाराशी जुळत नाही. योग्य फाइल निवडली आहे का ते तपासा.",
    },
    "POLYGLOT_FILE": {
        "en": "This file could not be accepted because it looks like more than one kind of file.",
        "hi": "यह फ़ाइल स्वीकार नहीं की जा सकी क्योंकि यह एक से अधिक प्रकार की फ़ाइल जैसी दिखती है।",
        "mr": "ही फाइल स्वीकारता आली नाही कारण ती एकापेक्षा जास्त प्रकारची फाइल वाटते.",
    },
    "CORRUPT_FILE": {
        "en": "This file is damaged or incomplete. Take the photo again or export the file again.",
        "hi": "यह फ़ाइल खराब या अधूरी है। फ़ोटो दोबारा लें या फ़ाइल फिर से बनाएं।",
        "mr": "ही फाइल खराब किंवा अपूर्ण आहे. फोटो पुन्हा घ्या किंवा फाइल पुन्हा तयार करा.",
    },
    "AUDIO_TOO_LONG": {
        "en": "The recording is too long. Keep voice notes under 5 minutes.",
        "hi": "रिकॉर्डिंग बहुत लंबी है। आवाज़ संदेश 5 मिनट से छोटा रखें।",
        "mr": "रेकॉर्डिंग खूप लांब आहे. आवाज संदेश 5 मिनिटांपेक्षा कमी ठेवा.",
    },
    "AUDIO_NO_SPEECH": {
        "en": "No speech was heard in the recording. Speak closer to the microphone, or type the symptoms.",
        "hi": "रिकॉर्डिंग में कोई आवाज़ नहीं सुनाई दी। माइक्रोफ़ोन के पास बोलें या लक्षण टाइप करें।",
        "mr": "रेकॉर्डिंगमध्ये आवाज ऐकू आला नाही. मायक्रोफोनजवळ बोला किंवा लक्षणे टाइप करा.",
    },
    "IMAGE_TOO_LARGE": {
        "en": "This image is too large to process. Take the photo at a lower resolution.",
        "hi": "यह चित्र बहुत बड़ा है। कम रिज़ॉल्यूशन पर फ़ोटो लें।",
        "mr": "हे चित्र खूप मोठे आहे. कमी रिझोल्यूशनवर फोटो घ्या.",
    },
    "PDF_ENCRYPTED": {
        "en": "This PDF is password-protected. Ask for an unprotected copy, or take a photo of the report.",
        "hi": "यह PDF पासवर्ड से सुरक्षित है। बिना पासवर्ड की प्रति मांगें या रिपोर्ट की फ़ोटो लें।",
        "mr": "हा PDF पासवर्डने सुरक्षित आहे. पासवर्डशिवाय प्रत मागा किंवा अहवालाचा फोटो घ्या.",
    },
    "PDF_TOO_MANY_PAGES": {
        "en": "This PDF has too many pages. Send only the pages with the test results.",
        "hi": "इस PDF में बहुत अधिक पेज हैं। केवल जांच परिणाम वाले पेज भेजें।",
        "mr": "या PDF मध्ये खूप पाने आहेत. फक्त तपासणी निकालांची पाने पाठवा.",
    },
    "PDF_UNREADABLE": {
        "en": "This PDF could not be read. Take a clear photo of the report instead.",
        "hi": "यह PDF पढ़ी नहीं जा सकी। इसके बजाय रिपोर्ट की साफ़ फ़ोटो लें।",
        "mr": "हा PDF वाचता आला नाही. त्याऐवजी अहवालाचा स्पष्ट फोटो घ्या.",
    },
    "ZIP_BOMB": {
        "en": "This archive expands to too much data. Send fewer images or a single scan series.",
        "hi": "यह संग्रह (ZIP) बहुत ज़्यादा डेटा में खुलता है। कम चित्र या एक ही स्कैन सीरीज़ भेजें।",
        "mr": "हे संग्रह (ZIP) खूप जास्त डेटामध्ये उघडते. कमी चित्रे किंवा एकच स्कॅन सिरीज पाठवा.",
    },
    "ZIP_PATH_TRAVERSAL": {
        "en": "This archive contains unsafe file names and was not opened.",
        "hi": "इस संग्रह (ZIP) में असुरक्षित फ़ाइल नाम हैं, इसलिए इसे नहीं खोला गया।",
        "mr": "या संग्रहात (ZIP) असुरक्षित फाइल नावे आहेत, म्हणून ते उघडले नाही.",
    },
    "DICOM_UNSUPPORTED_SOP": {
        "en": "This DICOM file is not an image (for example a report or structured data) and cannot be shown.",
        "hi": "यह DICOM फ़ाइल चित्र नहीं है (जैसे रिपोर्ट या संरचित डेटा) और दिखाई नहीं जा सकती।",
        "mr": "ही DICOM फाइल चित्र नाही (उदा. अहवाल किंवा संरचित डेटा) आणि दाखवता येत नाही.",
    },
    "DICOM_UNSUPPORTED_SYNTAX": {
        "en": "This scan uses a compression format that cannot be decoded here. Ask for an uncompressed export.",
        "hi": "यह स्कैन ऐसे संपीड़न प्रारूप में है जिसे यहाँ खोला नहीं जा सकता। बिना संपीड़न वाली प्रति मांगें।",
        "mr": "हा स्कॅन अशा कॉम्प्रेशन प्रकारात आहे जो येथे उघडता येत नाही. कॉम्प्रेशनशिवाय प्रत मागा.",
    },
    "DICOM_DEID_FAILED": {
        "en": "Identifying details could not be removed safely from this scan, so it was not stored.",
        "hi": "इस स्कैन से पहचान संबंधी जानकारी सुरक्षित रूप से हटाई नहीं जा सकी, इसलिए इसे सहेजा नहीं गया।",
        "mr": "या स्कॅनमधून ओळख पटवणारी माहिती सुरक्षितपणे काढता आली नाही, म्हणून तो जतन केला नाही.",
    },
    "BURNED_IN_PHI_UNMASKED": {
        "en": "This scan may show the patient's name on the image. It is kept out of automatic analysis.",
        "hi": "इस स्कैन के चित्र पर मरीज़ का नाम दिख सकता है। इसे स्वचालित विश्लेषण से बाहर रखा गया है।",
        "mr": "या स्कॅनच्या चित्रावर रुग्णाचे नाव दिसू शकते. ते स्वयंचलित विश्लेषणातून वगळले आहे.",
    },
    "MALWARE_DETECTED": {
        "en": "This file was blocked by the virus scanner.",
        "hi": "इस फ़ाइल को वायरस स्कैनर ने रोक दिया।",
        "mr": "ही फाइल व्हायरस स्कॅनरने रोखली.",
    },
    "QUEUE_FULL": {
        "en": "The system is busy. Emergency checks still work. Try the full assessment again in a moment.",
        "hi": "सिस्टम व्यस्त है। आपातकालीन जांच काम कर रही है। पूरा आकलन थोड़ी देर में फिर से करें।",
        "mr": "प्रणाली व्यस्त आहे. आपत्कालीन तपासणी चालू आहे. पूर्ण मूल्यांकन थोड्या वेळाने पुन्हा करा.",
    },
    "STORAGE_FULL": {
        "en": "This device is out of storage for patient files. Finish and erase old visits, then try again.",
        "hi": "इस डिवाइस में मरीज़ फ़ाइलों के लिए जगह नहीं है। पुरानी विज़िट पूरी करके मिटाएं, फिर प्रयास करें।",
        "mr": "या उपकरणात रुग्ण फाइलींसाठी जागा नाही. जुन्या भेटी पूर्ण करून पुसा, मग पुन्हा प्रयत्न करा.",
    },
    "JOB_TIMED_OUT": {
        "en": "This took too long and was stopped. Any results so far are shown. If symptoms are severe, call 108.",
        "hi": "इसमें बहुत समय लगा और इसे रोक दिया गया। अब तक के परिणाम दिखाए गए हैं। लक्षण गंभीर हों तो 108 पर कॉल करें।",
        "mr": "याला खूप वेळ लागला म्हणून ते थांबवले. आतापर्यंतचे निकाल दाखवले आहेत. लक्षणे गंभीर असल्यास 108 वर कॉल करा.",
    },
    "MODEL_UNAVAILABLE": {
        "en": "The AI model is offline. The rules-based assessment is shown. If symptoms are severe, call 108.",
        "hi": "एआई मॉडल ऑफ़लाइन है। नियम-आधारित आकलन दिखाया गया है। लक्षण गंभीर हों तो 108 पर कॉल करें।",
        "mr": "एआय मॉडेल ऑफलाइन आहे. नियमांवर आधारित मूल्यांकन दाखवले आहे. लक्षणे गंभीर असल्यास 108 वर कॉल करा.",
    },
    "BAD_REQUEST": {
        "en": "The request was not understood. Refresh the page and try again.",
        "hi": "अनुरोध समझ में नहीं आया। पेज रीफ़्रेश करके फिर से प्रयास करें।",
        "mr": "विनंती समजली नाही. पान रीफ्रेश करून पुन्हा प्रयत्न करा.",
    },
    "VALIDATION_ERROR": {
        "en": "Some details are missing or not valid. Check the highlighted fields.",
        "hi": "कुछ जानकारी गायब है या सही नहीं है। चिह्नित फ़ील्ड जांचें।",
        "mr": "काही माहिती गहाळ आहे किंवा चुकीची आहे. चिन्हांकित रकाने तपासा.",
    },
    "REQUEST_TOO_LARGE": {
        "en": "Too much data was sent at once. Shorten the text and try again.",
        "hi": "एक साथ बहुत ज़्यादा डेटा भेजा गया। टेक्स्ट छोटा करके फिर से भेजें।",
        "mr": "एकाच वेळी खूप जास्त डेटा पाठवला. मजकूर कमी करून पुन्हा पाठवा.",
    },
    "NO_FILE": {
        "en": "No file was received. Choose a file and try again.",
        "hi": "कोई फ़ाइल नहीं मिली। फ़ाइल चुनें और फिर से प्रयास करें।",
        "mr": "कोणतीही फाइल मिळाली नाही. फाइल निवडा आणि पुन्हा प्रयत्न करा.",
    },
    "MULTIPLE_FILES": {
        "en": "Send one file at a time.",
        "hi": "एक बार में एक ही फ़ाइल भेजें।",
        "mr": "एका वेळी एकच फाइल पाठवा.",
    },
    "EMPTY_FILE": {
        "en": "The file is empty. Choose another file.",
        "hi": "फ़ाइल खाली है। दूसरी फ़ाइल चुनें।",
        "mr": "फाइल रिकामी आहे. दुसरी फाइल निवडा.",
    },
    "TOO_MANY_ATTACHMENTS": {
        "en": "This visit already has the maximum number of files. Remove one to add another.",
        "hi": "इस विज़िट में पहले से अधिकतम फ़ाइलें हैं। नई जोड़ने के लिए एक हटाएं।",
        "mr": "या भेटीत आधीच कमाल फाइली आहेत. नवीन जोडण्यासाठी एक काढा.",
    },
    "INVALID_IDEMPOTENCY_KEY": {
        "en": "The request could not be matched safely. Refresh the page and try again.",
        "hi": "अनुरोध सुरक्षित रूप से मिलाया नहीं जा सका। पेज रीफ़्रेश करके फिर से प्रयास करें।",
        "mr": "विनंती सुरक्षितपणे जुळवता आली नाही. पान रीफ्रेश करून पुन्हा प्रयत्न करा.",
    },
    "IDEMPOTENCY_CONFLICT": {
        "en": "This request was already sent with different details. Refresh the page before trying again.",
        "hi": "यह अनुरोध पहले अलग जानकारी के साथ भेजा जा चुका है। फिर से प्रयास करने से पहले पेज रीफ़्रेश करें।",
        "mr": "ही विनंती आधी वेगळ्या माहितीसह पाठवली गेली आहे. पुन्हा प्रयत्न करण्यापूर्वी पान रीफ्रेश करा.",
    },
    "NOT_FOUND": {
        "en": "This record was not found. It may have been erased or expired.",
        "hi": "यह रिकॉर्ड नहीं मिला। हो सकता है इसे मिटा दिया गया हो या इसकी अवधि समाप्त हो गई हो।",
        "mr": "ही नोंद सापडली नाही. ती पुसली गेली असेल किंवा तिची मुदत संपली असेल.",
    },
    "METHOD_NOT_ALLOWED": {
        "en": "This action is not available here.",
        "hi": "यह कार्य यहाँ उपलब्ध नहीं है।",
        "mr": "ही क्रिया येथे उपलब्ध नाही.",
    },
    "STT_UNAVAILABLE": {
        "en": "Voice input is not available right now. Type the symptoms instead.",
        "hi": "आवाज़ से इनपुट अभी उपलब्ध नहीं है। इसके बजाय लक्षण टाइप करें।",
        "mr": "आवाजाने माहिती देणे सध्या उपलब्ध नाही. त्याऐवजी लक्षणे टाइप करा.",
    },
    "JOB_FAILED": {
        "en": "This step could not be completed. Try again. If symptoms are severe, call 108 now.",
        "hi": "यह चरण पूरा नहीं हो सका। फिर से प्रयास करें। लक्षण गंभीर हों तो तुरंत 108 पर कॉल करें।",
        "mr": "हा टप्पा पूर्ण होऊ शकला नाही. पुन्हा प्रयत्न करा. लक्षणे गंभीर असल्यास त्वरित 108 वर कॉल करा.",
    },
    "JOB_INTERRUPTED": {
        "en": "The device restarted while this was running. Try again. If symptoms are severe, call 108 now.",
        "hi": "यह चलते समय डिवाइस फिर से शुरू हो गया। फिर से प्रयास करें। लक्षण गंभीर हों तो तुरंत 108 पर कॉल करें।",
        "mr": "हे चालू असताना उपकरण पुन्हा सुरू झाले. पुन्हा प्रयत्न करा. लक्षणे गंभीर असल्यास त्वरित 108 वर कॉल करा.",
    },
    "INTERNAL_ERROR": {
        "en": "Something went wrong. Try again. If symptoms are severe, call 108 now.",
        "hi": "कुछ गड़बड़ हो गई। फिर से प्रयास करें। लक्षण गंभीर हों तो तुरंत 108 पर कॉल करें।",
        "mr": "काहीतरी चुकले. पुन्हा प्रयत्न करा. लक्षणे गंभीर असल्यास त्वरित 108 वर कॉल करा.",
    },
    "UNAUTHORIZED": {
        "en": "Please sign in again.",
        "hi": "कृपया फिर से साइन इन करें।",
        "mr": "कृपया पुन्हा साइन इन करा.",
    },
    "FORBIDDEN": {
        "en": "You do not have access to this record.",
        "hi": "आपको इस रिकॉर्ड तक पहुंच नहीं है।",
        "mr": "तुम्हाला या नोंदीचा प्रवेश नाही.",
    },
    "CSRF_FAILED": {
        "en": "Your session check failed. Refresh the page and try again.",
        "hi": "आपके सत्र की जांच विफल रही। पेज रीफ़्रेश करके फिर से प्रयास करें।",
        "mr": "तुमच्या सत्राची तपासणी अयशस्वी झाली. पान रीफ्रेश करून पुन्हा प्रयत्न करा.",
    },
    "RATE_LIMITED": {
        "en": "Too many attempts. Wait a little and try again.",
        "hi": "बहुत अधिक प्रयास। थोड़ा रुककर फिर से प्रयास करें।",
        "mr": "खूप जास्त प्रयत्न. थोडे थांबून पुन्हा प्रयत्न करा.",
    },
    "ACCOUNT_LOCKED": {
        "en": "This account is locked after too many failed sign-ins. Try again in 15 minutes or ask the admin.",
        "hi": "बहुत से असफल साइन-इन के बाद यह खाता बंद है। 15 मिनट बाद प्रयास करें या एडमिन से पूछें।",
        "mr": "अनेक अयशस्वी साइन-इननंतर हे खाते बंद आहे. 15 मिनिटांनी प्रयत्न करा किंवा अॅडमिनला विचारा.",
    },
    "CONSENT_REQUIRED": {
        "en": "Record the patient's consent before the full assessment. Emergency checks still run.",
        "hi": "पूरे आकलन से पहले मरीज़ की सहमति दर्ज करें। आपातकालीन जांच फिर भी चलती है।",
        "mr": "पूर्ण मूल्यांकनापूर्वी रुग्णाची संमती नोंदवा. आपत्कालीन तपासणी तरीही चालते.",
    },
}

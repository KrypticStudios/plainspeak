"""Labels for the results page in every language, so someone who can't read English can still find their way."""

from datetime import date

from babel.dates import format_date

KEYS = ["urgent", "soon", "not_urgent", "means", "read_aloud", "not_sure", "dates", "no_date", "add_calendar",
        "todo", "money", "contact", "rights", "talk_person", "show_original", "save", "saved", "found",
        "not_found", "from"]

TEXT = {
    "en": ["Urgent", "Soon", "Not urgent", "What this letter means", "Read this out loud", "Things we're not sure about",
           "Important dates", "No exact date given", "Add these dates to my calendar", "What to do", "Money",
           "Who to contact", "Your rights (from the letter)", "Talk to a real person about this.",
           "Show the full original letter", "Save to My letters", "Saved to My letters.", "found in your letter",
           "we could not find these words in your letter. Please double-check.", "From"],
    "es": ["Urgente", "Pronto", "No es urgente", "Qué significa esta carta", "Leer en voz alta", "Cosas de las que no estamos seguros",
           "Fechas importantes", "No hay una fecha exacta", "Agregar estas fechas a mi calendario", "Qué hacer", "Dinero",
           "A quién contactar", "Sus derechos (según la carta)", "Hable con una persona sobre esto.",
           "Ver la carta original completa", "Guardar en Mis cartas", "Guardado en Mis cartas.", "está en su carta",
           "no encontramos estas palabras en su carta. Por favor revise.", "De"],
    "zh-CN": ["紧急", "尽快", "不紧急", "这封信是什么意思", "朗读", "我们不确定的地方",
              "重要日期", "没有确切日期", "把这些日期加入我的日历", "要做什么", "钱",
              "联系谁", "您的权利（信中提到的）", "请找真人咨询这件事。",
              "显示完整原信", "保存到我的信件", "已保存到我的信件。", "在您的信中找到",
              "我们在您的信中找不到这些字，请再检查一下。", "发件人"],
    "vi": ["Khẩn cấp", "Sớm", "Không khẩn cấp", "Lá thư này có nghĩa là gì", "Đọc to", "Những điều chúng tôi chưa chắc",
           "Ngày quan trọng", "Không có ngày cụ thể", "Thêm các ngày này vào lịch của tôi", "Cần làm gì", "Tiền",
           "Liên hệ ai", "Quyền của bạn (theo lá thư)", "Hãy nói chuyện với một người thật về việc này.",
           "Xem toàn bộ lá thư gốc", "Lưu vào Thư của tôi", "Đã lưu vào Thư của tôi.", "có trong thư của bạn",
           "chúng tôi không tìm thấy những chữ này trong thư. Vui lòng kiểm tra lại.", "Từ"],
    "ar": ["عاجل", "قريبًا", "غير عاجل", "ماذا تعني هذه الرسالة", "اقرأها بصوت عالٍ", "أشياء لسنا متأكدين منها",
           "تواريخ مهمة", "لا يوجد تاريخ محدد", "أضف هذه التواريخ إلى تقويمي", "ماذا تفعل", "المال",
           "بمن تتصل", "حقوقك (كما في الرسالة)", "تحدث مع شخص حقيقي بشأن هذا.",
           "اعرض الرسالة الأصلية كاملة", "احفظ في رسائلي", "تم الحفظ في رسائلي.", "موجود في رسالتك",
           "لم نجد هذه الكلمات في رسالتك. يرجى التحقق.", "من"],
    "hi": ["ज़रूरी", "जल्दी", "ज़रूरी नहीं", "इस पत्र का मतलब क्या है", "ज़ोर से पढ़ें", "जिन बातों पर हमें पक्का यकीन नहीं",
           "ज़रूरी तारीखें", "कोई तय तारीख नहीं दी गई", "ये तारीखें मेरे कैलेंडर में जोड़ें", "क्या करना है", "पैसे",
           "किससे संपर्क करें", "आपके अधिकार (पत्र के अनुसार)", "इस बारे में किसी असली व्यक्ति से बात करें।",
           "पूरा मूल पत्र दिखाएँ", "मेरे पत्रों में सहेजें", "मेरे पत्रों में सहेजा गया।", "आपके पत्र में मिला",
           "ये शब्द आपके पत्र में नहीं मिले। कृपया दोबारा जाँचें।", "भेजने वाला"],
    "tl": ["Apurahan", "Malapit na", "Hindi apurahan", "Ano ang ibig sabihin ng sulat na ito", "Basahin nang malakas",
           "Mga bagay na hindi kami sigurado", "Mahahalagang petsa", "Walang eksaktong petsa",
           "Idagdag ang mga petsang ito sa aking kalendaryo", "Ano ang gagawin", "Pera", "Sino ang kokontakin",
           "Ang iyong mga karapatan (mula sa sulat)", "Makipag-usap sa isang tao tungkol dito.",
           "Ipakita ang buong orihinal na sulat", "I-save sa Aking mga sulat", "Na-save sa Aking mga sulat.",
           "nasa iyong sulat", "hindi namin nakita ang mga salitang ito sa iyong sulat. Pakisuri muli.", "Mula sa"],
    "fr": ["Urgent", "Bientôt", "Pas urgent", "Ce que signifie cette lettre", "Lire à voix haute", "Ce dont nous ne sommes pas sûrs",
           "Dates importantes", "Pas de date précise", "Ajouter ces dates à mon calendrier", "Que faire", "Argent",
           "Qui contacter", "Vos droits (selon la lettre)", "Parlez-en à une vraie personne.",
           "Afficher la lettre originale complète", "Enregistrer dans Mes lettres", "Enregistré dans Mes lettres.",
           "trouvé dans votre lettre", "nous n'avons pas trouvé ces mots dans votre lettre. Veuillez vérifier.", "De"],
    "ko": ["긴급", "곧", "급하지 않음", "이 편지의 뜻", "소리 내어 읽기", "확실하지 않은 부분",
           "중요한 날짜", "정확한 날짜 없음", "이 날짜들을 내 달력에 추가", "해야 할 일", "돈",
           "연락할 곳", "당신의 권리 (편지에 적힌 내용)", "이 일은 실제 사람과 상담하세요.",
           "원본 편지 전체 보기", "내 편지에 저장", "내 편지에 저장되었습니다.", "편지에서 확인됨",
           "편지에서 이 문장을 찾지 못했습니다. 다시 확인해 주세요.", "보낸 곳"],
    "ru": ["Срочно", "Скоро", "Не срочно", "Что означает это письмо", "Прочитать вслух", "В чём мы не уверены",
           "Важные даты", "Точная дата не указана", "Добавить эти даты в мой календарь", "Что делать", "Деньги",
           "Куда обращаться", "Ваши права (из письма)", "Поговорите об этом с живым человеком.",
           "Показать всё исходное письмо", "Сохранить в Мои письма", "Сохранено в Мои письма.", "есть в вашем письме",
           "мы не нашли эти слова в вашем письме. Пожалуйста, проверьте.", "От"],
    "pt": ["Urgente", "Em breve", "Não é urgente", "O que esta carta significa", "Ler em voz alta", "Coisas de que não temos certeza",
           "Datas importantes", "Sem data exata", "Adicionar estas datas ao meu calendário", "O que fazer", "Dinheiro",
           "Quem contatar", "Seus direitos (segundo a carta)", "Fale com uma pessoa sobre isso.",
           "Mostrar a carta original completa", "Salvar em Minhas cartas", "Salvo em Minhas cartas.", "está na sua carta",
           "não encontramos estas palavras na sua carta. Por favor, confira.", "De"],
}




def friendly_date(value: str, lang_code: str) -> str | None:
    """'2026-12-04' -> 'viernes, 4 de diciembre de 2026'. None if it isn't a real date."""
    try:
        d = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return format_date(d, format="full", locale=lang_code.replace("-", "_"))


# Labels added later. {n} is replaced with a number of days.
EXTRA_KEYS = ["days_left", "due_today", "passed", "next_deadline", "print", "start_over", "free_help", "first_step"]
EXTRA = {
    "en": ["{n} days left", "Due TODAY", "This date has passed. Call them now.", "Next deadline",
           "Save or print this summary", "Explain another letter", "Free help near you", "Do this first"],
    "es": ["Quedan {n} días", "Vence HOY", "Esta fecha ya pasó. Llame ahora.", "Próxima fecha límite",
           "Guardar o imprimir este resumen", "Explicar otra carta", "Ayuda gratis cerca de usted", "Haga esto primero"],
    "zh-CN": ["还剩 {n} 天", "今天截止", "这个日期已经过了，请马上打电话。", "下一个截止日期",
              "保存或打印这份摘要", "解释另一封信", "您附近的免费帮助", "先做这一步"],
    "vi": ["Còn {n} ngày", "Hạn chót HÔM NAY", "Ngày này đã qua. Hãy gọi ngay.", "Hạn chót tiếp theo",
           "Lưu hoặc in bản tóm tắt này", "Giải thích lá thư khác", "Trợ giúp miễn phí gần bạn", "Làm việc này trước"],
    "ar": ["باقي {n} يوم", "الموعد اليوم", "هذا التاريخ قد مضى. اتصل بهم الآن.", "الموعد النهائي التالي",
           "احفظ أو اطبع هذا الملخص", "اشرح رسالة أخرى", "مساعدة مجانية قريبة منك", "افعل هذا أولاً"],
    "hi": ["{n} दिन बाकी", "आज आखिरी दिन", "यह तारीख निकल गई है। अभी फ़ोन करें।", "अगली आखिरी तारीख",
           "यह सारांश सहेजें या प्रिंट करें", "दूसरा पत्र समझाएँ", "आपके पास मुफ़्त मदद", "पहले यह करें"],
    "tl": ["{n} araw na lang", "Ngayon ang huling araw", "Lumipas na ang petsang ito. Tumawag na ngayon.", "Susunod na deadline",
           "I-save o i-print ang buod na ito", "Ipaliwanag ang ibang sulat", "Libreng tulong malapit sa iyo", "Gawin muna ito"],
    "fr": ["Plus que {n} jours", "Échéance AUJOURD'HUI", "Cette date est passée. Appelez maintenant.", "Prochaine échéance",
           "Enregistrer ou imprimer ce résumé", "Expliquer une autre lettre", "Aide gratuite près de chez vous", "Faites d'abord ceci"],
    "ko": ["{n}일 남음", "오늘 마감", "이 날짜는 지났습니다. 지금 전화하세요.", "다음 마감일",
           "이 요약 저장 또는 인쇄", "다른 편지 설명하기", "가까운 무료 도움", "먼저 이것부터 하세요"],
    "ru": ["Осталось дней: {n}", "Срок СЕГОДНЯ", "Эта дата прошла. Позвоните сейчас.", "Ближайший срок",
           "Сохранить или распечатать", "Объяснить другое письмо", "Бесплатная помощь рядом", "Сначала сделайте это"],
    "pt": ["Faltam {n} dias", "Vence HOJE", "Esta data já passou. Ligue agora.", "Próximo prazo",
           "Salvar ou imprimir este resumo", "Explicar outra carta", "Ajuda gratuita perto de você", "Faça isto primeiro"],
}



def labels(lang_code: str) -> dict[str, str]:
    """All labels for a language as a dictionary, e.g. labels('es')['todo'] -> 'Qué hacer'."""
    result = dict(zip(KEYS, TEXT.get(lang_code, TEXT["en"])))
    result.update(zip(EXTRA_KEYS, EXTRA.get(lang_code, EXTRA["en"])))
    result.update(zip(ASK_KEYS, ASK.get(lang_code, ASK["en"])))
    return result


# Labels for "Ask a question".
ASK_KEYS = ["ask_title", "ask_placeholder", "ask_button", "not_in_letter", "who_to_ask", "suggested"]
ASK = {
    "en": ["Ask a question about this letter", "For example: What happens if I miss the deadline?", "Ask",
           "The letter doesn't say this.", "Who can answer", "Common questions"],
    "es": ["Haga una pregunta sobre esta carta", "Por ejemplo: ¿Qué pasa si no cumplo la fecha límite?", "Preguntar",
           "La carta no dice esto.", "Quién puede responder", "Preguntas comunes"],
    "zh-CN": ["关于这封信提个问题", "例如：如果我错过截止日期会怎样？", "提问",
              "信中没有提到这一点。", "谁可以回答", "常见问题"],
    "vi": ["Đặt câu hỏi về lá thư này", "Ví dụ: Điều gì xảy ra nếu tôi trễ hạn?", "Hỏi",
           "Lá thư không nói điều này.", "Ai có thể trả lời", "Câu hỏi thường gặp"],
    "ar": ["اسأل سؤالاً عن هذه الرسالة", "مثلاً: ماذا يحدث إذا فاتني الموعد؟", "اسأل",
           "الرسالة لا تذكر هذا.", "من يمكنه الإجابة", "أسئلة شائعة"],
    "hi": ["इस पत्र के बारे में सवाल पूछें", "जैसे: अगर मैं आखिरी तारीख चूक जाऊँ तो क्या होगा?", "पूछें",
           "पत्र में यह नहीं लिखा है।", "कौन जवाब दे सकता है", "आम सवाल"],
    "tl": ["Magtanong tungkol sa sulat na ito", "Halimbawa: Ano ang mangyayari kung lumampas ako sa deadline?", "Magtanong",
           "Hindi ito sinasabi ng sulat.", "Sino ang makakasagot", "Mga karaniwang tanong"],
    "fr": ["Poser une question sur cette lettre", "Par exemple : que se passe-t-il si je rate la date limite ?", "Demander",
           "La lettre ne le dit pas.", "Qui peut répondre", "Questions fréquentes"],
    "ko": ["이 편지에 대해 질문하기", "예: 마감일을 놓치면 어떻게 되나요?", "질문하기",
           "편지에 이 내용은 없습니다.", "답해 줄 수 있는 곳", "자주 묻는 질문"],
    "ru": ["Задать вопрос об этом письме", "Например: что будет, если я пропущу срок?", "Спросить",
           "В письме об этом не сказано.", "Кто может ответить", "Частые вопросы"],
    "pt": ["Faça uma pergunta sobre esta carta", "Por exemplo: o que acontece se eu perder o prazo?", "Perguntar",
           "A carta não diz isso.", "Quem pode responder", "Perguntas comuns"],
}

# Generic questions offered when there is no ready-made list (live AI answers).
GENERIC_QUESTIONS = ["What happens if I miss the deadline?", "Can I get help paying?",
                     "What documents do I need?", "Who should I call first?"]

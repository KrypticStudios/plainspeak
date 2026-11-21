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


def labels(lang_code: str) -> dict[str, str]:
    """All labels for a language as a dictionary, e.g. labels('es')['todo'] -> 'Qué hacer'."""
    return dict(zip(KEYS, TEXT.get(lang_code, TEXT["en"])))


def friendly_date(value: str, lang_code: str) -> str | None:
    """'2026-12-04' -> 'viernes, 4 de diciembre de 2026'. None if it isn't a real date."""
    try:
        d = date.fromisoformat(value.strip())
    except ValueError:
        return None
    return format_date(d, format="full", locale=lang_code.replace("-", "_"))

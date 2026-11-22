import streamlit as st
from uuid import uuid4
from dotenv import load_dotenv
from langgraph.types import Command
from langgraph.checkpoint.memory import MemorySaver
from graph.workflow import build_graph

load_dotenv()

st.set_page_config(page_title="SchoolTrip AI", page_icon="🎒", layout="wide")

st.markdown(
    """
    <style>
        .stApp { direction: rtl; text-align: right; }
        [data-testid="stSidebar"] { direction: rtl; text-align: right; }
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stMultiSelect > div > div { direction: rtl; }
        h1, h2, h3, p, li, label { direction: rtl; text-align: right; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_graph():
    return build_graph(MemorySaver())


if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
    st.session_state.stage = "input"
    st.session_state.interrupt_data = None
    st.session_state.error = None
    st.session_state.show_balloons = False
    st.session_state.pending_action = None

graph = get_graph()
config = {"configurable": {"thread_id": st.session_state.thread_id}}


def get_interrupt_value(snapshot):
    try:
        return snapshot.tasks[0].interrupts[0].value
    except (IndexError, AttributeError):
        return None


def advance_stage(snapshot):
    if not snapshot.next:
        st.session_state.stage = "final"
        st.session_state.show_balloons = True
    else:
        next_node = snapshot.next[0]
        if next_node == "ask_clarification":
            st.session_state.stage = "clarification"
            st.session_state.interrupt_data = get_interrupt_value(snapshot)
        elif next_node == "teacher_review":
            st.session_state.stage = "review"
            st.session_state.interrupt_data = get_interrupt_value(snapshot)
        else:
            st.session_state.stage = "final"
            st.session_state.show_balloons = True


# --- Process pending actions BEFORE rendering ---
if st.session_state.pending_action is not None:
    action = st.session_state.pending_action
    st.session_state.pending_action = None
    action_type = action["type"]

    try:
        if action_type == "initial":
            graph.invoke(action["state"], config)
            snapshot = graph.get_state(config)
            advance_stage(snapshot)

        elif action_type == "clarification":
            graph.invoke(Command(resume=action["answers"]), config)
            snapshot = graph.get_state(config)
            advance_stage(snapshot)

        elif action_type == "approve":
            graph.invoke(
                Command(resume={"approved": True, "feedback": ""}), config
            )
            st.session_state.stage = "final"
            st.session_state.show_balloons = True

        elif action_type == "revise":
            graph.invoke(
                Command(resume={"approved": False, "feedback": action["feedback"]}),
                config,
            )
            snapshot = graph.get_state(config)
            advance_stage(snapshot)

    except Exception as e:
        st.session_state.error = f"שגיאה: {e}"


# --- Sidebar ---
with st.sidebar:
    st.header("שלבי התכנון")
    stages_map = {
        "input": "📝 הזנת פרטים",
        "clarification": "❓ שאלות הבהרה",
        "review": "👀 סקירת מסלול",
        "final": "✅ תוכנית סופית",
    }
    for key, label in stages_map.items():
        if key == st.session_state.stage:
            st.markdown(f"**→ {label}**")
        else:
            st.markdown(f"&nbsp;&nbsp;&nbsp;{label}")

    st.divider()
    if st.button("🔄 התחל מחדש"):
        st.session_state.thread_id = str(uuid4())
        st.session_state.stage = "input"
        st.session_state.interrupt_data = None
        st.session_state.error = None
        st.session_state.show_balloons = False
        st.session_state.pending_action = None
        st.cache_resource.clear()
        st.rerun()

# --- Title ---
st.title("🎒 SchoolTrip AI")
st.subheader("מערכת AI לתכנון טיולים לבתי ספר")

if st.session_state.error:
    st.error(st.session_state.error)
    st.session_state.error = None

# ========== STAGE: INPUT ==========
if st.session_state.stage == "input":
    st.info("מלאו את הפרטים הבאים כדי שנוכל לתכנן עבורכם טיול מותאם אישית. "
            "בחרו כיתה, מספר תלמידים, תקציב, אזור ותחומי עניין.")

    with st.form("trip_form"):
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox(
                "כיתה",
                [""] + ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י", "יא", "יב"],
                index=0,
                help="בחרו את שכבת הגיל של הכיתה",
            )
            budget = st.number_input(
                "תקציב לתלמיד (₪)",
                min_value=0,
                value=0,
                step=10,
                help="התקציב המקסימלי לתלמיד בודד בשקלים",
            )
            duration = st.selectbox(
                "משך הטיול",
                [""] + [
                    "חצי יום (3-4 שעות)",
                    "יום שלם (6-8 שעות)",
                    "יומיים",
                    "שלושה ימים",
                ],
                index=0,
                help="בחרו את משך הטיול הרצוי",
            )
        with col2:
            students = st.number_input(
                "מספר תלמידים",
                min_value=0,
                value=0,
                step=1,
                help="מספר התלמידים המשתתפים בטיול",
            )
            region = st.selectbox(
                "אזור",
                [""] + ["כל הארץ", "צפון", "מרכז", "דרום", "ירושלים", "שפלה", "חוף"],
                index=0,
                help="בחרו את האזור הגיאוגרפי המועדף",
            )
            interests = st.multiselect(
                "תחומי עניין",
                [
                    "טבע", "היסטוריה", "ספורט", "מדע", "אמנות",
                    "ארכיאולוגיה", "חיות", "מים", "חינוך", "תרבות",
                ],
                default=[],
                help="בחרו תחום עניין אחד או יותר לטיול",
            )
        constraints = st.text_area(
            "בקשות ומגבלות מיוחדות",
            placeholder="למשל: תלמיד עם כיסא גלגלים, ללא הליכה ממושכת...",
            help="ציינו מגבלות מיוחדות כגון נגישות, אלרגיות וכו׳",
        )
        submitted = st.form_submit_button(
            "🚀 תכנן טיול", use_container_width=True
        )

    if submitted:
        missing = []
        if not grade:
            missing.append("כיתה")
        if students <= 0:
            missing.append("מספר תלמידים")
        if budget <= 0:
            missing.append("תקציב לתלמיד")
        if not region:
            missing.append("אזור")
        if not duration:
            missing.append("משך הטיול")

        if missing:
            st.warning(f"אנא מלאו את השדות הבאים: {', '.join(missing)}")
        else:
            st.session_state.pending_action = {
                "type": "initial",
                "state": {
                    "grade": grade,
                    "students_count": students,
                    "budget_per_student": float(budget),
                    "region": region,
                    "duration": duration,
                    "interests": interests,
                    "constraints": constraints,
                },
            }
            st.rerun()

# ========== STAGE: CLARIFICATION ==========
elif st.session_state.stage == "clarification":
    st.header("❓ שאלות הבהרה")
    st.info("חסרים פרטים. אנא השלם את המידע הבא:")

    interrupt_data = st.session_state.interrupt_data or {}
    questions = interrupt_data.get("questions", [])

    with st.form("clarification_form"):
        answers = {}
        for q in questions:
            field = q["field"]
            question_text = q["question"]
            if field == "students_count":
                answers[field] = st.number_input(question_text, min_value=1, value=30)
            elif field == "budget_per_student":
                answers[field] = st.number_input(
                    question_text, min_value=10.0, value=100.0, step=10.0
                )
            elif field == "grade":
                answers[field] = st.selectbox(
                    question_text,
                    ["א", "ב", "ג", "ד", "ה", "ו", "ז", "ח", "ט", "י", "יא", "יב"],
                )
            elif field == "region":
                answers[field] = st.selectbox(
                    question_text,
                    ["כל הארץ", "צפון", "מרכז", "דרום", "ירושלים", "שפלה", "חוף"],
                )
            elif field == "duration":
                answers[field] = st.selectbox(
                    question_text,
                    ["חצי יום (3-4 שעות)", "יום שלם (6-8 שעות)", "יומיים", "שלושה ימים"],
                )
            else:
                answers[field] = st.text_input(question_text)

        submitted = st.form_submit_button("📤 שלח", use_container_width=True)

    if submitted:
        st.session_state.pending_action = {
            "type": "clarification",
            "answers": answers,
        }
        st.rerun()

# ========== STAGE: REVIEW ==========
elif st.session_state.stage == "review":
    st.header("👀 סקירת מסלול מוצע")

    snapshot = graph.get_state(config)
    state = snapshot.values

    destinations = state.get("selected_destinations", [])
    if destinations:
        with st.expander("🗺️ יעדים שנבחרו", expanded=False):
            for dest in destinations:
                st.markdown(
                    f"**{dest['name']}** ({dest['region']}) — "
                    f"₪{dest['estimated_cost']} | {dest.get('duration_hours', '?')} שעות"
                )
                st.caption(dest.get("description", ""))

    st.markdown("---")
    st.markdown(state.get("itinerary", "אין מסלול"))
    st.markdown("---")

    with st.form("review_form"):
        st.markdown("**מה דעתך על המסלול?**")
        action = st.radio(
            "בחר פעולה:",
            ["✅ אשר מסלול", "🔄 בקש שינויים"],
            index=0,
            horizontal=True,
        )
        feedback = st.text_area(
            "הערות לשינוי (אם רלוונטי)",
            placeholder="פרט מה ברצונך לשנות...",
        )
        submitted = st.form_submit_button("שלח", use_container_width=True)

    if submitted:
        if action == "✅ אשר מסלול":
            st.session_state.pending_action = {"type": "approve"}
            st.rerun()
        else:
            if not feedback:
                st.warning("אנא פרט מה ברצונך לשנות")
            else:
                st.session_state.pending_action = {
                    "type": "revise",
                    "feedback": feedback,
                }
                st.rerun()

# ========== STAGE: FINAL ==========
elif st.session_state.stage == "final":
    snapshot = graph.get_state(config)
    state = snapshot.values

    if not state.get("selected_destinations"):
        st.warning(
            "לא נמצאו יעדים מתאימים לקריטריונים שהוזנו. "
            "נסה לשנות את האזור, התקציב או טווח הגילאים."
        )
    else:
        st.header("✅ תוכנית טיול סופית")
        st.success("המסלול אושר!")

        if st.session_state.show_balloons:
            st.balloons()
            st.session_state.show_balloons = False

        st.markdown(state.get("itinerary", ""))

        st.markdown("---")
        st.subheader("📋 סיכום")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("כיתה", state.get("grade", ""))
            st.metric("תלמידים", state.get("students_count", 0))
        with c2:
            st.metric("תקציב לתלמיד", f"₪{state.get('budget_per_student', 0):.0f}")
            st.metric("אזור", state.get("region", ""))
        with c3:
            st.metric("משך", state.get("duration", ""))
            st.metric("יעדים", len(state.get("selected_destinations", [])))

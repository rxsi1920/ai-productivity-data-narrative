import streamlit as st

from narrative.story import GROUP_QUESTION

# One line per page: what part of the group question it answers.
PAGE_BLURBS = {
    "profitability": "Does AI pay for itself?",
    "feedback-loop": "Is AI weakening the human practice and knowledge that both people and AI learn from?",
    "moral-degradation": "What does AI cost in judgement, responsibility and trust?",
    "overall-conclusion": "Weighing the measured gains against the hidden costs.",
}


def render_landing(pages):
    st.title("The Rise of Artificial Intelligence")
    st.subheader(GROUP_QUESTION)
    st.markdown("Each page takes one side of the question. Start with profitability:")

    cols = st.columns(len(pages))
    for col, page in zip(cols, pages):
        with col:
            with st.container(border=True):
                st.page_link(page, label=page.title)
                st.caption(PAGE_BLURBS.get(page.url_path, ""))
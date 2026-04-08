import anthropic


def ask_claude(question, chunks, api_key):
    client = anthropic.Anthropic(api_key=api_key)

    if chunks:
        context = '\n\n'.join([
            f"[From {c['filename']}]\n{c['text']}"
            for c in chunks
        ])
        system_prompt = (
            "You are a study assistant. Answer the question using the provided study materials. "
            "If the materials don't fully cover the question, say so and supplement with general knowledge.\n\n"
            f"Study materials:\n{context}"
        )
    else:
        system_prompt = (
            "You are a study assistant. No study materials were found for this topic. "
            "Answer from general knowledge and note that no vault content was available."
        )

    message = client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1024,
        system=system_prompt,
        messages=[{'role': 'user', 'content': question}]
    )

    sources = list(dict.fromkeys(c['filename'] for c in chunks))
    return {
        'answer': message.content[0].text,
        'sources': sources
    }

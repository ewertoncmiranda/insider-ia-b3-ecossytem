"""Gerador das fichas pre-calculadas de anos fechados (SPEC 6.3; TASK-IA-07/08).

    python -m app.fichas --tipo todas            # evidencia, setores, ativos, mercado
    python -m app.fichas --tipo evidencia --ate-ano 2025

Le o MySQL so com o usuario leitor_ia (DEC-IA-05) e grava conhecimento/**.md
apenas quando o hash muda.
"""

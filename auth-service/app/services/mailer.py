def send_reset_email(email: str, link: str) -> None:
    """Fase 3: só loga o link no stdout do container (sem envio real) — o
    ponto de entrada certo já fica pronto pra fase 4 trocar isso por SMTP
    de verdade (Mailtrap em dev, Brevo em produção) sem mexer em mais nada
    além desta função."""
    print(f"[mailer STUB] Redefinição de senha para {email}: {link}", flush=True)

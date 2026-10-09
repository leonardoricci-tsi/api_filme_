export interface StatusPremium {
  premium: boolean;
  // Plano pago ativo (nerd / stalker_do_tomhanks), ou null no gratuito.
  plano: string | null;
}

export interface CheckoutResposta {
  checkout_url: string;
}

export type PlanoPago = 'nerd' | 'stalker_do_tomhanks';

export interface QuizRodada {
  round_id: string;
  opcoes: string[];
  imagem_base64: string;
}

export interface QuizRespostaPayload {
  round_id: string;
  resposta: string;
}

export interface QuizResposta {
  correto: boolean;
  resposta_certa: string;
  sinopse: string;
  poster_url: string | null;
  data_lancamento: string | null;
  nota: number | null;
}

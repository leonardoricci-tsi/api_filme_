export interface Movie {
  tmdb_movie_id: number;
  titulo: string;
  sinopse: string;
  poster_url: string | null;
  data_lancamento: string | null;
  nota: number | null;
}

export interface PaginaFilmes {
  itens: Movie[];
  total: number;
  pagina: number;
  tamanho_pagina: number;
  total_paginas: number;
}

export interface Ator {
  nome: string;
  personagem: string;
  foto_url: string | null;
}

export interface Provedor {
  nome: string;
  logo_url: string | null;
  tipo: 'assinatura' | 'aluguel' | 'compra';
}

export interface DetalhesFilme {
  elenco: Ator[];
  onde_assistir: Provedor[];
}

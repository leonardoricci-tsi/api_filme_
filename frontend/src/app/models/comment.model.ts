export interface MovieComment {
  id: number;
  tmdb_movie_id: number;
  titulo: string | null;
  poster_path: string | null;
  texto: string;
  criado_em: string;
}

export interface CommentPayload {
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
  texto: string;
}

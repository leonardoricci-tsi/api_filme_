export interface Favorite {
  id: number;
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
  criado_em: string;
}

export interface FavoritePayload {
  tmdb_movie_id: number;
  titulo: string;
  poster_path: string | null;
}

export interface Movie {
  tmdb_movie_id: number;
  titulo: string;
  sinopse: string;
  poster_url: string | null;
  data_lancamento: string | null;
}

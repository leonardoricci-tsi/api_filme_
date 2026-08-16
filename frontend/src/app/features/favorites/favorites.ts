import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';

import { FavoritesService } from '../../core/services/favorites.service';
import { Favorite } from '../../models/favorite.model';
import { MovieCard } from '../../shared/movie-card/movie-card';

@Component({
  selector: 'app-favorites',
  standalone: true,
  imports: [CommonModule, MovieCard],
  templateUrl: './favorites.html',
  styleUrl: './favorites.css',
})
export class Favorites implements OnInit {
  favoritos = signal<Favorite[]>([]);
  carregando = signal(true);

  constructor(private readonly favoritesService: FavoritesService) {}

  ngOnInit(): void {
    this.carregarFavoritos();
  }

  private carregarFavoritos(): void {
    this.carregando.set(true);
    this.favoritesService.listar().subscribe({
      next: (favoritos) => {
        this.favoritos.set(favoritos);
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }

  posterUrl(posterPath: string | null): string | null {
    return posterPath ? `https://image.tmdb.org/t/p/w500${posterPath}` : null;
  }

  remover(favorito: Favorite): void {
    // Atualização otimista: some da lista na hora, sem esperar um novo GET.
    this.favoritos.update((atual) => atual.filter((f) => f.id !== favorito.id));
    this.favoritesService.remover(favorito.id).subscribe({
      error: () => this.carregarFavoritos(), // reverte pro estado real se falhar
    });
  }
}

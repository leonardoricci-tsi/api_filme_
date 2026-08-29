import { CommonModule } from '@angular/common';
import { Component, OnInit, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../core/services/auth.service';
import { MoviesService } from '../../core/services/movies.service';
import { Movie } from '../../models/movie.model';

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.html',
  styleUrl: './landing.css',
})
export class Landing implements OnInit {
  filmes = signal<Movie[]>([]);
  carregando = signal(true);

  constructor(
    private readonly moviesService: MoviesService,
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    if (this.authService.isAuthenticated()) {
      this.router.navigate(['/app']);
      return;
    }

    this.moviesService.listar().subscribe({
      next: (filmes) => {
        this.filmes.set(filmes.slice(0, 10));
        this.carregando.set(false);
      },
      error: () => this.carregando.set(false),
    });
  }
}

import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './login.html',
  styleUrl: '../auth-shared.css',
})
export class Login {
  email = '';
  senha = '';
  erro = signal('');
  carregando = signal(false);

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  entrar(): void {
    this.erro.set('');
    this.carregando.set(true);

    this.authService.login({ email: this.email, senha: this.senha }).subscribe({
      next: () => {
        this.carregando.set(false);
        this.router.navigate(['/']);
      },
      error: (erro) => {
        this.carregando.set(false);
        this.erro.set(erro?.error?.detail ?? 'Não foi possível entrar.');
      },
    });
  }
}

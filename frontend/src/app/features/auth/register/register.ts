import { CommonModule } from '@angular/common';
import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/services/auth.service';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.html',
  styleUrl: '../auth-shared.css',
})
export class Register {
  nome = '';
  email = '';
  senha = '';
  erro = signal('');
  carregando = signal(false);

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  cadastrar(): void {
    this.erro.set('');
    this.carregando.set(true);

    this.authService
      .register({ nome: this.nome, email: this.email, senha: this.senha })
      .subscribe({
        next: () => {
          this.carregando.set(false);
          this.router.navigate(['/']);
        },
        error: (erro) => {
          this.carregando.set(false);
          this.erro.set(erro?.error?.detail ?? 'Não foi possível cadastrar.');
        },
      });
  }
}

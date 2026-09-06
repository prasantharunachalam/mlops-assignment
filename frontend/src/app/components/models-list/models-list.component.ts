import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { Model } from '../../models';
import { ModelService } from '../../services';
import { CreateModelDialogComponent } from '../create-model-dialog/create-model-dialog.component';

@Component({
  selector: 'app-models-list',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatDialogModule
  ],
  templateUrl: './models-list.component.html',
  styleUrl: './models-list.component.scss'
})
export class ModelsListComponent implements OnInit {
  models: Model[] = [];
  loading = false;

  constructor(
    private modelService: ModelService,
    private router: Router,
    private dialog: MatDialog
  ) {}

  ngOnInit() {
    this.loadModels();
  }

  loadModels() {
    this.loading = true;
    this.modelService.listModels().subscribe({
      next: (response) => {
        this.models = response.items;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading models:', error);
        this.loading = false;
      }
    });
  }

  viewModel(modelId: string) {
    this.router.navigate(['/models', modelId]);
  }

  openCreateDialog() {
    const dialogRef = this.dialog.open(CreateModelDialogComponent, {
      width: '500px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadModels();
      }
    });
  }
}

import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Model, ModelVersion, LifecycleStage } from '../../models';
import { ModelService } from '../../services';
import { CreateVersionDialogComponent } from '../create-version-dialog/create-version-dialog.component';

@Component({
  selector: 'app-model-detail',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './model-detail.component.html',
  styleUrl: './model-detail.component.scss'
})
export class ModelDetailComponent implements OnInit {
  model: Model | null = null;
  versions: ModelVersion[] = [];
  loading = false;
  modelId: string | null = null;

  lifecycleStages = Object.values(LifecycleStage);
  Object = Object; // Make Object available in template

  constructor(
    private route: ActivatedRoute,
    private modelService: ModelService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.modelId = this.route.snapshot.paramMap.get('id');
    if (this.modelId) {
      this.loadModel(this.modelId);
      this.loadVersions(this.modelId);
    }
  }

  loadModel(modelId: string) {
    this.loading = true;
    this.modelService.getModel(modelId).subscribe({
      next: (model) => {
        this.model = model;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading model:', error);
        this.loading = false;
      }
    });
  }

  loadVersions(modelId: string) {
    this.modelService.listVersions(modelId).subscribe({
      next: (response) => {
        this.versions = response.items;
      },
      error: (error) => {
        console.error('Error loading versions:', error);
      }
    });
  }

  openCreateVersionDialog() {
    if (!this.modelId) return;

    const dialogRef = this.dialog.open(CreateVersionDialogComponent, {
      width: '600px',
      data: { modelId: this.modelId }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result && this.modelId) {
        this.loadVersions(this.modelId);
        this.snackBar.open('Version created successfully', 'Close', { duration: 3000 });
      }
    });
  }

  promoteLifecycle(version: ModelVersion, targetStage: LifecycleStage) {
    if (!this.modelId) return;

    this.modelService.promoteLifecycle(this.modelId, version.id, {
      target_stage: targetStage,
      row_version: version.row_version
    }).subscribe({
      next: () => {
        this.snackBar.open(`Lifecycle promoted to ${targetStage}`, 'Close', { duration: 3000 });
        if (this.modelId) {
          this.loadVersions(this.modelId);
        }
      },
      error: (err) => {
        const errorMsg = err.error?.error?.message || err.error?.message || 'Failed to promote lifecycle';
        this.snackBar.open(errorMsg, 'Close', { duration: 5000 });
        console.error('Error promoting lifecycle:', err);
      }
    });
  }

  getStageColor(stage: LifecycleStage): string {
    switch (stage) {
      case LifecycleStage.PRODUCTION:
        return 'primary';
      case LifecycleStage.STAGING:
        return 'accent';
      case LifecycleStage.APPROVED:
        return 'accent';
      default:
        return '';
    }
  }

  canPromoteTo(currentStage: LifecycleStage, targetStage: LifecycleStage): boolean {
    // Valid lifecycle transitions matching backend state machine
    const validTransitions: Record<LifecycleStage, LifecycleStage[]> = {
      [LifecycleStage.DRAFT]: [LifecycleStage.VALIDATED],
      [LifecycleStage.VALIDATED]: [LifecycleStage.APPROVED, LifecycleStage.DRAFT],
      [LifecycleStage.APPROVED]: [LifecycleStage.STAGING, LifecycleStage.VALIDATED],
      [LifecycleStage.STAGING]: [LifecycleStage.PRODUCTION, LifecycleStage.APPROVED],
      [LifecycleStage.PRODUCTION]: [LifecycleStage.ARCHIVED, LifecycleStage.STAGING],
      [LifecycleStage.ARCHIVED]: []
    };

    const allowedStages = validTransitions[currentStage] || [];
    return allowedStages.includes(targetStage);
  }
}

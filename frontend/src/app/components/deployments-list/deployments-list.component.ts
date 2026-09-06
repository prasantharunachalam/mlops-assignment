import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Deployment } from '../../models';
import { DeploymentService } from '../../services';
import { CreateDeploymentDialogComponent } from '../create-deployment-dialog/create-deployment-dialog.component';

@Component({
  selector: 'app-deployments-list',
  standalone: true,
  imports: [
    CommonModule,
    MatTableModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatSnackBarModule
  ],
  templateUrl: './deployments-list.component.html',
  styleUrl: './deployments-list.component.scss'
})
export class DeploymentsListComponent implements OnInit {
  deployments: Deployment[] = [];
  loading = false;
  displayedColumns: string[] = ['id', 'model_version_id', 'environment', 'status', 'requested_at', 'actions'];

  constructor(
    private deploymentService: DeploymentService,
    private dialog: MatDialog,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit() {
    this.loadDeployments();
  }

  loadDeployments() {
    this.loading = true;
    this.deploymentService.listDeployments().subscribe({
      next: (response) => {
        this.deployments = response.items;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading deployments:', error);
        this.loading = false;
      }
    });
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'SUCCEEDED': return 'primary';
      case 'FAILED': return 'warn';
      case 'DEPLOYING': return 'accent';
      default: return '';
    }
  }

  openCreateDialog() {
    const dialogRef = this.dialog.open(CreateDeploymentDialogComponent, {
      width: '550px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadDeployments();
        this.snackBar.open('Deployment created successfully', 'Close', { duration: 3000 });
      }
    });
  }

  retryDeployment(deployment: Deployment) {
    this.deploymentService.retryDeployment(deployment.id).subscribe({
      next: () => {
        this.snackBar.open('Deployment retry initiated', 'Close', { duration: 3000 });
        this.loadDeployments();
      },
      error: (err) => {
        const errorMsg = err.error?.error?.message || err.error?.message || 'Failed to retry deployment';
        this.snackBar.open(errorMsg, 'Close', { duration: 5000 });
        console.error('Error retrying deployment:', err);
      }
    });
  }

  rollbackDeployment(deployment: Deployment) {
    if (confirm(`Are you sure you want to rollback deployment ${deployment.id}?`)) {
      this.deploymentService.rollbackDeployment(deployment.id).subscribe({
        next: () => {
          this.snackBar.open('Rollback initiated', 'Close', { duration: 3000 });
          this.loadDeployments();
        },
        error: (err) => {
          const errorMsg = err.error?.error?.message || err.error?.message || 'Failed to rollback deployment';
          this.snackBar.open(errorMsg, 'Close', { duration: 5000 });
          console.error('Error rolling back deployment:', err);
        }
      });
    }
  }

  canRetry(deployment: Deployment): boolean {
    return deployment.status === 'FAILED';
  }

  canRollback(deployment: Deployment): boolean {
    return deployment.status === 'SUCCEEDED';
  }
}

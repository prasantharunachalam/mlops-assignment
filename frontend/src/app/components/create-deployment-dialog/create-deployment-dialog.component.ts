import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { DeploymentService, ModelService } from '../../services';
import { DeploymentCreate } from '../../models';
import { v4 as uuidv4 } from 'uuid';

@Component({
  selector: 'app-create-deployment-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule
  ],
  templateUrl: './create-deployment-dialog.component.html',
  styleUrl: './create-deployment-dialog.component.scss'
})
export class CreateDeploymentDialogComponent implements OnInit {
  deploymentForm: FormGroup;
  loading = false;
  error: string | null = null;
  modelVersions: Array<{ id: string; model_name: string; version_number: string; lifecycle_stage: string }> = [];
  loadingVersions = false;

  environments = ['development', 'staging', 'production'];

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<CreateDeploymentDialogComponent>,
    private deploymentService: DeploymentService,
    private modelService: ModelService
  ) {
    this.deploymentForm = this.fb.group({
      model_version_id: ['', [Validators.required]],
      environment: ['', [Validators.required]]
    });
  }

  ngOnInit() {
    this.loadModelVersions();
  }

  loadModelVersions() {
    this.loadingVersions = true;
    // Load all models and their versions
    this.modelService.listModels().subscribe({
      next: (response) => {
        // For each model, load its versions
        const versionPromises = response.items.map(model =>
          new Promise((resolve) => {
            this.modelService.listVersions(model.id).subscribe({
              next: (versionResponse) => {
                const versions = versionResponse.items.map(v => ({
                  id: v.id,
                  model_name: model.name,
                  version_number: v.version_number,
                  lifecycle_stage: v.lifecycle_stage
                }));
                resolve(versions);
              },
              error: () => resolve([])
            });
          })
        );

        Promise.all(versionPromises).then((allVersions: any) => {
          this.modelVersions = allVersions.flat();
          this.loadingVersions = false;
        });
      },
      error: (err) => {
        console.error('Error loading models:', err);
        this.loadingVersions = false;
      }
    });
  }

  onSubmit() {
    if (this.deploymentForm.valid) {
      this.loading = true;
      this.error = null;

      const deploymentData: DeploymentCreate = {
        model_version_id: this.deploymentForm.value.model_version_id,
        environment: this.deploymentForm.value.environment,
        idempotency_key: uuidv4() // Generate UUID for idempotency
      };

      this.deploymentService.createDeployment(deploymentData).subscribe({
        next: (deployment) => {
          this.loading = false;
          this.dialogRef.close(deployment);
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.error?.message || err.error?.message || 'Failed to create deployment';
          console.error('Error creating deployment:', err);
        }
      });
    }
  }

  onCancel() {
    this.dialogRef.close();
  }

  getVersionDisplay(version: any): string {
    return `${version.model_name} v${version.version_number} (${version.lifecycle_stage})`;
  }
}

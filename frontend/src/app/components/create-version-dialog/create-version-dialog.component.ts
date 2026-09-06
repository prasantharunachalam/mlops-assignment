import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { ModelService } from '../../services';
import { ModelVersionCreate } from '../../models';

@Component({
  selector: 'app-create-version-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule
  ],
  templateUrl: './create-version-dialog.component.html',
  styleUrl: './create-version-dialog.component.scss'
})
export class CreateVersionDialogComponent {
  versionForm: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<CreateVersionDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: { modelId: string },
    private modelService: ModelService
  ) {
    this.versionForm = this.fb.group({
      version_number: ['', [Validators.required, Validators.minLength(1)]],
      framework: ['', [Validators.required, Validators.minLength(1)]],
      algorithm: [''],
      artifact_uri: ['', [Validators.required, Validators.minLength(1)]],
      training_data_ref: [''],
      tags: ['']
    });
  }

  onSubmit() {
    if (this.versionForm.valid) {
      this.loading = true;
      this.error = null;

      const formValue = this.versionForm.value;

      // Parse tags from JSON string if provided
      let tags = {};
      if (formValue.tags) {
        try {
          tags = JSON.parse(formValue.tags);
        } catch (e) {
          this.error = 'Tags must be valid JSON';
          this.loading = false;
          return;
        }
      }

      const versionData: ModelVersionCreate = {
        version_number: formValue.version_number,
        framework: formValue.framework,
        algorithm: formValue.algorithm || undefined,
        artifact_uri: formValue.artifact_uri,
        training_data_ref: formValue.training_data_ref || undefined,
        tags: tags
      };

      this.modelService.createVersion(this.data.modelId, versionData).subscribe({
        next: (version) => {
          this.loading = false;
          this.dialogRef.close(version);
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.error?.message || err.error?.message || 'Failed to create version';
          console.error('Error creating version:', err);
        }
      });
    }
  }

  onCancel() {
    this.dialogRef.close();
  }
}

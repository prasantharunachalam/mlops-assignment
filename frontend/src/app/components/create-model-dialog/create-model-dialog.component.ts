import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { ModelService } from '../../services';
import { ModelCreate } from '../../models';

@Component({
  selector: 'app-create-model-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule
  ],
  templateUrl: './create-model-dialog.component.html',
  styleUrl: './create-model-dialog.component.scss'
})
export class CreateModelDialogComponent {
  modelForm: FormGroup;
  loading = false;
  error: string | null = null;

  constructor(
    private fb: FormBuilder,
    private dialogRef: MatDialogRef<CreateModelDialogComponent>,
    private modelService: ModelService
  ) {
    this.modelForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(1)]],
      description: [''],
      owner: ['', [Validators.required, Validators.minLength(1)]]
    });
  }

  onSubmit() {
    if (this.modelForm.valid) {
      this.loading = true;
      this.error = null;

      const modelData: ModelCreate = this.modelForm.value;

      this.modelService.createModel(modelData).subscribe({
        next: (model) => {
          this.loading = false;
          this.dialogRef.close(model);
        },
        error: (err) => {
          this.loading = false;
          this.error = err.error?.error?.message || err.error?.message || 'Failed to create model';
          console.error('Error creating model:', err);
        }
      });
    }
  }

  onCancel() {
    this.dialogRef.close();
  }
}

import { ReactNode } from "react";

type FieldProps = {
  label: string;
  required?: boolean;
  children: ReactNode;
};

export function Field({ label, required, children }: FieldProps) {
  return (
    <label className="field">
      <span>
        {label}
        {required && <b> *</b>}
      </span>
      {children}
    </label>
  );
}

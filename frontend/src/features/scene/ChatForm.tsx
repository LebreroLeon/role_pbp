import { FormEvent } from "react";
import { Button } from "../../components/ui";

type ChatFormProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent) => void;
  placeholder: string;
  disabled: boolean;
};

export function ChatForm({ value, onChange, onSubmit, placeholder, disabled }: ChatFormProps) {
  return (
    <form className="chat-form" onSubmit={onSubmit}>
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder={placeholder} disabled={disabled} />
      <Button type="submit" disabled={disabled || !value.trim()}>
        Enviar
      </Button>
    </form>
  );
}

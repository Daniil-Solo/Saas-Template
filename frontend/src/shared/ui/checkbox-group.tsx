import { useId } from "react";

export type CheckboxOption = {
  value: number;
  label: string;
};

type CheckboxGroupProps = {
  legend: string;
  options: CheckboxOption[];
  value: number[];
  onChange: (value: number[]) => void;
  disabled?: boolean;
};

export function CheckboxGroup({ legend, options, value, onChange, disabled }: CheckboxGroupProps) {
  const groupId = useId();

  function toggle(optionValue: number, checked: boolean) {
    onChange(checked ? [...value, optionValue] : value.filter((item) => item !== optionValue));
  }

  return (
    <fieldset className="flex flex-col gap-2" disabled={disabled}>
      <legend className="mb-1 text-sm font-medium">{legend}</legend>
      {options.map((option) => {
        const id = `${groupId}-${option.value}`;
        return (
          <div key={option.value} className="flex items-center gap-2 text-sm">
            <input
              id={id}
              type="checkbox"
              className="size-4"
              checked={value.includes(option.value)}
              onChange={(event) => toggle(option.value, event.target.checked)}
            />
            <label htmlFor={id}>{option.label}</label>
          </div>
        );
      })}
    </fieldset>
  );
}

import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
}
  
export const Input: React.FC<InputProps> = ({
    label,
    error,
    className = '',
    id,
    name,
    autoComplete,
    ...props
}) => {
    // IDが指定されていない場合、nameから生成
    const inputId = id || (name ? `input-${name}` : undefined);
    // autoCompleteが指定されていない場合、適切なデフォルト値を設定
    const defaultAutoComplete = autoComplete !== undefined ? autoComplete : 'off';

    return (
        <div className="space-y-1">
            {label && (
                <label htmlFor={inputId} className="text-sm font-medium text-slate-700">
                    {label}
                </label>
            )}
            <input
                id={inputId}
                name={name}
                autoComplete={defaultAutoComplete}
                className={`w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 ${error ? 'border-red-500' : ''} ${className}`}
                {...props}
            />
            {error && (
                <p className="text-sm text-red-500">{error}</p>
            )}
        </div>
    );
};
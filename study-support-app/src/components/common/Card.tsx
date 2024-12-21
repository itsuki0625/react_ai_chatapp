interface CardProps {
    children: React.ReactNode;
    className?: string;
}
  
export const Card: React.FC<CardProps> = ({
    children,
    className = ''
}) => {
    return (
        <div className={`rounded-lg border border-slate-200 bg-white shadow-sm ${className}`}>
            {children}
        </div>
    );
};
  
export const CardHeader: React.FC<CardProps> = ({
    children,
    className = ''
}) => {
    return (
        <div className={`px-6 py-4 border-b border-slate-200 ${className}`}>
            {children}
        </div>
    );
};
  
export const CardContent: React.FC<CardProps> = ({
    children,
    className = ''
}) => {
    return (
        <div className={`px-6 py-4 ${className}`}>
            {children}
        </div>
    );
};
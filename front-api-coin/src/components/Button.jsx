import { useState } from 'react';

const Button = ({ 
  children, 
  type = 'button', 
  onClick, 
  disabled = false, 
  loading = false,
  variant = 'primary', // primary, secondary, danger, success
  size = 'medium', // small, medium, large
  fullWidth = false,
  icon: Icon,
  className = ''
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const baseClasses = `
    relative inline-flex items-center justify-center
    font-medium rounded-2xl transition-all duration-200
    focus:outline-none focus:ring-4 focus:ring-offset-2
    disabled:opacity-60 disabled:cursor-not-allowed
    transform active:scale-[0.98]
    shadow-lg hover:shadow-xl
    ${fullWidth ? 'w-full' : ''}
    ${className}
  `;

  const variants = {
    primary: `
      bg-gradient-to-r from-blue-600 to-indigo-600 
      hover:from-blue-700 hover:to-indigo-700
      text-white border-0
      focus:ring-blue-500/50
      shadow-blue-500/25 hover:shadow-blue-500/40
    `,
    secondary: `
      bg-gradient-to-r from-gray-100 to-gray-200 
      hover:from-gray-200 hover:to-gray-300
      text-gray-700 border-0
      focus:ring-gray-500/50
      shadow-gray-500/25 hover:shadow-gray-500/40
    `,
    danger: `
      bg-gradient-to-r from-red-500 to-red-600 
      hover:from-red-600 hover:to-red-700
      text-white border-0
      focus:ring-red-500/50
      shadow-red-500/25 hover:shadow-red-500/40
    `,
    success: `
      bg-gradient-to-r from-emerald-500 to-teal-600 
      hover:from-emerald-600 hover:to-teal-700
      text-white border-0
      focus:ring-emerald-500/50
      shadow-emerald-500/25 hover:shadow-emerald-500/40
    `
  };

  const sizes = {
    small: 'px-4 py-2 text-sm',
    medium: 'px-6 py-3 text-base',
    large: 'px-8 py-4 text-lg'
  };

  const handleMouseDown = () => setIsPressed(true);
  const handleMouseUp = () => setIsPressed(false);
  const handleMouseLeave = () => setIsPressed(false);

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseLeave}
      className={`
        ${baseClasses}
        ${variants[variant]}
        ${sizes[size]}
        ${isPressed ? 'scale-[0.98]' : 'hover:-translate-y-0.5'}
        ${loading ? 'cursor-wait' : ''}
      `}
    >
      {/* Loading Spinner */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center">
          <svg className="animate-spin h-5 w-5 text-current" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      )}

      {/* Content */}
      <div className={`flex items-center space-x-2 ${loading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-200`}>
        {Icon && <Icon className="h-5 w-5" />}
        <span>{children}</span>
      </div>

      {/* Ripple Effect */}
      <div className="absolute inset-0 rounded-2xl overflow-hidden">
        <div className={`
          absolute inset-0 bg-white/20 transform scale-0 rounded-full
          transition-transform duration-300 origin-center
          ${isPressed ? 'scale-100' : ''}
        `} />
      </div>
    </button>
  );
};

export default Button;

import { useState } from 'react';

const InputField = ({ 
  label, 
  type = 'text', 
  name, 
  value, 
  onChange, 
  placeholder, 
  required = false, 
  icon: Icon,
  error = null,
  helpText = null,
  min = null,
  max = null
}) => {
  const [focused, setFocused] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const hasValue = value && value.length > 0;
  const isFloatingLabel = focused || hasValue;

  return (
    <div className="relative group">
      <div className="relative">
        {/* Icon */}
        {Icon && (
          <div className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors duration-200 z-10 ${
            focused ? 'text-blue-500' : 'text-gray-400'
          }`}>
            <Icon className="h-5 w-5" />
          </div>
        )}

        {/* Input */}
        <input
          type={type === 'password' && showPassword ? 'text' : type}
          name={name}
          value={value}
          onChange={onChange}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          required={required}
          min={min}
          max={max}
          className={`
            peer w-full h-14 px-4 ${Icon ? 'pl-12' : 'pl-4'} ${type === 'password' ? 'pr-12' : 'pr-4'}
            bg-white/70 backdrop-blur-sm
            border-2 rounded-2xl
            transition-all duration-300 ease-in-out
            text-gray-900 text-base
            placeholder-transparent
            shadow-sm
            ${focused 
              ? 'border-blue-500 shadow-lg shadow-blue-500/25 bg-white' 
              : error 
                ? 'border-red-400 shadow-lg shadow-red-500/20 bg-red-50/50'
                : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
            }
            ${error ? 'focus:border-red-500 focus:shadow-red-500/25' : 'focus:border-blue-500 focus:shadow-blue-500/25'}
            focus:outline-none focus:ring-0
          `}
          placeholder={placeholder}
        />

        {/* Floating Label */}
        <label
          className={`
            absolute left-4 ${Icon ? 'left-12' : 'left-4'} 
            transition-all duration-300 ease-in-out
            pointer-events-none
            ${isFloatingLabel 
              ? `${Icon ? '-top-3 left-8' : '-top-3 left-4'} text-sm px-2 bg-white rounded-md ${focused ? 'text-blue-600' : error ? 'text-red-600' : 'text-gray-600'}` 
              : 'top-1/2 -translate-y-1/2 text-gray-500'
            }
            ${focused && !error ? 'text-blue-600 font-medium' : ''}
            ${error ? 'text-red-600' : ''}
          `}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>

        {/* Password Toggle */}
        {type === 'password' && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className={`absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors duration-200 ${
              focused ? 'text-blue-500' : ''
            }`}
          >
            {showPassword ? (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
              </svg>
            ) : (
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            )}
          </button>
        )}

        {/* Focus Ring */}
        <div className={`
          absolute inset-0 rounded-2xl transition-all duration-300
          ${focused ? 'ring-4 ring-blue-500/20' : ''}
          ${error && focused ? 'ring-4 ring-red-500/20' : ''}
          pointer-events-none
        `} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-2 flex items-center text-red-600 text-sm animate-slideIn">
          <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {error}
        </div>
      )}

      {/* Helper Text */}
      {!error && helpText && (
        <div className="mt-2 text-sm text-gray-500 animate-fadeIn">
          {helpText}
        </div>
      )}
    </div>
  );
};

export default InputField;

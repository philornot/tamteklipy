// Reusable styled components używające design tokens

// ============================================
// BUTTONS
// ============================================

export const Button = ({
  variant = 'primary',
  size = 'md',
  children,
  className = '',
  ...props
}) => {
  const baseClasses = 'font-medium rounded-button transition-all duration-300 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-purple-500 hover:bg-purple-600 text-white shadow-glow-sm hover:shadow-glow',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white border border-gray-600',
    accent: 'bg-fuchsia-500 hover:bg-fuchsia-600 text-white shadow-glow-sm hover:shadow-glow',
    danger: 'bg-red-500 hover:bg-red-600 text-white',
    success: 'bg-green-500 hover:bg-green-600 text-white',
    ghost: 'bg-transparent hover:bg-gray-700 text-gray-300 border border-transparent hover:border-purple-500',
    outline: 'bg-transparent hover:bg-purple-500/10 text-purple-400 border border-purple-500 hover:border-purple-400',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variants[variant]} ${sizes[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

// ============================================
// CARDS
// ============================================

export const Card = ({
  variant = 'default',
  hoverable = false,
  selected = false,
  children,
  className = '',
  ...props
}) => {
  const baseClasses = 'bg-gray-800 rounded-card border transition-all duration-300';

  const variants = {
    default: 'border-gray-700',
    elevated: 'border-gray-700 shadow-card',
    glow: 'border-purple-500/30 shadow-glow',
  };

  const hoverClass = hoverable ? 'hover:border-purple-500/50 hover:shadow-card-hover cursor-pointer' : '';
  const selectedClass = selected ? 'border-purple-500 shadow-glow bg-purple-500/10' : '';

  return (
    <div
      className={`${baseClasses} ${variants[variant]} ${hoverClass} ${selectedClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

// ============================================
// MODALS
// ============================================

export const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  className = '',
  maxWidth = 'max-w-2xl',
  ...props
}) => {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 animate-fade-in"
      onClick={onClose}
    >
      <div
        className={`bg-gray-800 rounded-modal border border-gray-700 ${maxWidth} w-full max-h-[90vh] overflow-y-auto ${className}`}
        onClick={(e) => e.stopPropagation()}
        {...props}
      >
        {title && (
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className="text-xl font-bold">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-button transition"
            >
              ✕
            </button>
          </div>
        )}
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

// ============================================
// INPUTS
// ============================================

export const Input = ({
  label,
  error,
  className = '',
  containerClassName = '',
  ...props
}) => {
  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-gray-300 mb-2 text-sm font-medium">
          {label}
        </label>
      )}
      <input
        className={`input-field ${error ? 'border-red-500' : 'border-gray-600'} ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};

export const Textarea = ({
  label,
  error,
  className = '',
  containerClassName = '',
  ...props
}) => {
  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-gray-300 mb-2 text-sm font-medium">
          {label}
        </label>
      )}
      <textarea
        className={`input-field ${error ? 'border-red-500' : 'border-gray-600'} resize-none ${className}`}
        {...props}
      />
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};

export const Select = ({
  label,
  error,
  options = [],
  className = '',
  containerClassName = '',
  ...props
}) => {
  return (
    <div className={containerClassName}>
      {label && (
        <label className="block text-gray-300 mb-2 text-sm font-medium">
          {label}
        </label>
      )}
      <select
        className={`input-field ${error ? 'border-red-500' : 'border-gray-600'} ${className}`}
        {...props}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && (
        <p className="mt-1 text-sm text-red-500">{error}</p>
      )}
    </div>
  );
};

// ============================================
// BADGES
// ============================================

export const Badge = ({
  variant = 'default',
  children,
  className = '',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center gap-1 px-2 py-1 rounded-badge text-xs font-medium';

  const variants = {
    default: 'bg-gray-700 text-gray-300',
    primary: 'bg-purple-500 text-white',
    accent: 'bg-fuchsia-500 text-white',
    success: 'bg-green-500 text-white',
    warning: 'bg-yellow-500 text-white',
    danger: 'bg-red-500 text-white',
    info: 'bg-blue-500 text-white',
    outline: 'bg-transparent border border-purple-500 text-purple-400',
  };

  return (
    <span
      className={`${baseClasses} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
};

// ============================================
// LOADING SPINNER
// ============================================

export const Spinner = ({
  size = 'md',
  color = 'primary',
  className = '',
  ...props
}) => {
  const sizes = {
    sm: 'w-4 h-4 border-2',
    md: 'w-6 h-6 border-2',
    lg: 'w-8 h-8 border-3',
    xl: 'w-12 h-12 border-4',
  };

  const colors = {
    primary: 'border-purple-500/30 border-t-purple-500',
    accent: 'border-fuchsia-500/30 border-t-fuchsia-500',
    white: 'border-white/30 border-t-white',
  };

  return (
    <div
      className={`${sizes[size]} ${colors[color]} rounded-full animate-spin ${className}`}
      {...props}
    />
  );
};

// ============================================
// SECTION HEADER (Pattern z Dashboard)
// ============================================

export const SectionHeader = ({
  title,
  subtitle,
  action,
  gradient = false,
  className = '',
  ...props
}) => {
  return (
    <div className={`mb-8 relative ${className}`} {...props}>
      {/* Glow effects */}
      <div className="absolute -left-20 -top-20 w-64 h-64 bg-purple-500/5 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -right-20 -top-10 w-80 h-80 bg-fuchsia-500/5 rounded-full blur-3xl pointer-events-none" />

      <div className={`relative rounded-2xl p-6 border border-purple-500/20 backdrop-blur-sm transition-all duration-200 ${gradient ? 'bg-gradient-card' : 'bg-gray-800/50'}`}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-4xl font-bold ${gradient ? 'gradient-text-primary' : ''} drop-shadow-lg`}>
              {title}
            </h1>
            {subtitle && (
              <p className="text-gray-400 text-sm mt-2">{subtitle}</p>
            )}
          </div>

          {action && (
            <div>{action}</div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================
// CHECKBOX (Styled)
// ============================================

export const Checkbox = ({
  checked,
  onChange,
  label,
  className = '',
  ...props
}) => {
  return (
    <label className={`flex items-center gap-2 cursor-pointer ${className}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="w-4 h-4 rounded border-gray-600 bg-gray-700 text-purple-500 focus:ring-purple-500 focus:ring-offset-gray-800"
        {...props}
      />
      {label && <span className="text-gray-300">{label}</span>}
    </label>
  );
};
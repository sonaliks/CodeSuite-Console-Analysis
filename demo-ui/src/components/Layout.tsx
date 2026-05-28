import type { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden font-aws">
      {/* Sidebar Navigation */}
      <nav
        className="aws-nav w-60 flex-shrink-0 flex flex-col"
        aria-label="Service navigation"
      >
        {/* Service Header */}
        <div className="px-4 py-3 border-b border-aws-nav-hover">
          <h1 className="text-white text-base font-bold leading-tight">CodeSuite</h1>
          <p className="text-gray-400 text-aws-small mt-0.5">Diagnostics Demo</p>
        </div>

        {/* Navigation Items - compact spacing matching AWS console */}
        <ul className="flex-1 py-1" role="list">
          <li>
            <a
              href="#"
              className="aws-nav-item active block text-sm"
              aria-current="page"
            >
              CodePipeline
            </a>
          </li>
          <li>
            <a href="#" className="aws-nav-item block text-sm">
              CodeCommit
            </a>
          </li>
          <li>
            <a href="#" className="aws-nav-item block text-sm">
              CodeDeploy
            </a>
          </li>
          <li>
            <a href="#" className="aws-nav-item block text-sm">
              CodeBuild
            </a>
          </li>
        </ul>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-aws-nav-hover text-gray-400 text-xs">
          AWS Console Demo
        </div>
      </nav>

      {/* Right side: Header + Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header Bar */}
        <header className="bg-white border-b border-aws-border px-6 py-2.5 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-3">
            <span className="inline-block w-1 h-5 bg-aws-orange rounded-aws-sm" aria-hidden="true"></span>
            <h2 className="text-lg font-bold text-aws-text leading-tight">CodePipeline</h2>
          </div>
          <div className="text-sm text-aws-text-secondary">
            us-east-1
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 overflow-auto bg-aws-bg-secondary p-6">
          {children}
        </main>
      </div>
    </div>
  );
}

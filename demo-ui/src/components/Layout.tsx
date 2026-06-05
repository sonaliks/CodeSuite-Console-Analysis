import type { ReactNode } from 'react';

export type NavPage = 'pipeline' | 'codedeploy' | 'codebuild';

interface LayoutProps {
  children: ReactNode;
  activePage: NavPage;
  onNavigate: (page: NavPage) => void;
}

const NAV_ITEMS: { id: NavPage; label: string }[] = [
  { id: 'pipeline', label: 'CodePipeline' },
  { id: 'codedeploy', label: 'CodeDeploy' },
  { id: 'codebuild', label: 'CodeBuild' },
];

const PAGE_TITLES: Record<NavPage, string> = {
  pipeline: 'CodePipeline',
  codedeploy: 'CodeDeploy',
  codebuild: 'CodeBuild',
};

export function Layout({ children, activePage, onNavigate }: LayoutProps) {
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

        {/* Navigation Items */}
        <ul className="flex-1 py-1" role="list">
          {NAV_ITEMS.map((item) => (
            <li key={item.id}>
              <button
                onClick={() => onNavigate(item.id)}
                className={`aws-nav-item block text-sm w-full text-left ${
                  activePage === item.id ? 'active' : ''
                }`}
                aria-current={activePage === item.id ? 'page' : undefined}
              >
                {item.label}
              </button>
            </li>
          ))}
          <li>
            <span className="aws-nav-item block text-sm opacity-50 cursor-default">
              CodeCommit
            </span>
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
            <h2 className="text-lg font-bold text-aws-text leading-tight">
              {PAGE_TITLES[activePage]}
            </h2>
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

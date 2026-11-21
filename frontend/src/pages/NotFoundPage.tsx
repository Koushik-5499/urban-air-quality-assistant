import { Link } from 'react-router-dom';
import { AlertTriangle, Home } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { ROUTES } from '../constants/routes';

export function NotFoundPage() {
  useDocumentTitle('Page Not Found');

  return (
    <div className="max-w-md mx-auto pt-16">
      <Card variant="standard" className="text-center shadow-lg">
        <CardHeader className="items-center pb-2">
          <div className="p-3.5 rounded-2xl bg-rose-50 text-rose-600 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200 dark:border-rose-900/60 mb-3 shadow-xs">
            <AlertTriangle className="w-8 h-8" aria-hidden="true" />
          </div>
          <Badge variant="danger" size="sm" showDot className="mb-2">
            404 Error
          </Badge>
          <CardTitle className="text-xl">Page Not Found</CardTitle>
          <CardDescription>
            The requested air quality route does not exist or has been relocated within the atmospheric telemetry system.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-4 space-y-4">
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Please check the URL or return to the main dashboard.
          </p>
          <Link to={ROUTES.DASHBOARD} className="inline-block">
            <Button variant="primary" size="md">
              <Home className="w-4 h-4 mr-2" aria-hidden="true" />
              Return to Dashboard
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}

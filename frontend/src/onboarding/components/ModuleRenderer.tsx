import { FileText, Video, File, HelpCircle, ExternalLink } from 'lucide-react';
import { Card, CardContent, Button } from '@/core/components/ui';
import type { OnboardingModule, ModuleProgress } from '@/core/types';

interface ModuleRendererProps {
  module: OnboardingModule;
  progress?: ModuleProgress;
  onComplete: () => void;
  isCompleting?: boolean;
}

const moduleIcons = {
  text: FileText,
  video: Video,
  document: File,
  quiz: HelpCircle,
  link: ExternalLink,
};

export function ModuleRenderer({
  module,
  progress,
  onComplete,
  isCompleting,
}: ModuleRendererProps) {
  const Icon = moduleIcons[module.module_type];
  const isCompleted = progress?.status === 'completed';

  const renderContent = () => {
    switch (module.module_type) {
      case 'text':
        return (
          <div
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{
              __html: (module.content_data.content as string) || '',
            }}
          />
        );

      case 'video':
        return (
          <div className="aspect-video bg-black rounded-lg overflow-hidden">
            <video
              src={module.content_data.url as string}
              controls
              className="w-full h-full"
            />
          </div>
        );

      case 'document':
        return (
          <div className="space-y-4">
            <p className="text-muted-foreground">
              {module.content_data.description as string}
            </p>
            <a
              href={module.content_data.url as string}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-primary hover:underline"
            >
              <File className="h-4 w-4" />
              Descargar documento
            </a>
          </div>
        );

      case 'link':
        return (
          <div className="space-y-4">
            <p className="text-muted-foreground">
              {module.content_data.description as string}
            </p>
            <a
              href={module.content_data.url as string}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-primary hover:underline"
            >
              <ExternalLink className="h-4 w-4" />
              Abrir enlace
            </a>
          </div>
        );

      case 'quiz':
        return (
          <div className="space-y-4">
            <p className="text-muted-foreground">
              Este módulo contiene un cuestionario.
            </p>
            {/* Quiz implementation would go here */}
          </div>
        );

      default:
        return <p>Tipo de módulo no soportado</p>;
    }
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start gap-4 mb-6">
          <div className="rounded-full bg-primary/10 p-3">
            <Icon className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-semibold">{module.title}</h2>
            {module.description && (
              <p className="text-muted-foreground mt-1">{module.description}</p>
            )}
            {module.estimated_duration_minutes && (
              <p className="text-sm text-muted-foreground mt-2">
                Duración estimada: {module.estimated_duration_minutes} min
              </p>
            )}
          </div>
        </div>

        <div className="mb-6">{renderContent()}</div>

        {!isCompleted && (
          <Button
            className="w-full"
            onClick={onComplete}
            isLoading={isCompleting}
          >
            Marcar como completado
          </Button>
        )}

        {isCompleted && (
          <div className="text-center text-green-600 font-medium">
            Módulo completado
          </div>
        )}
      </CardContent>
    </Card>
  );
}

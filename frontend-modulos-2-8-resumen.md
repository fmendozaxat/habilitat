# Frontend Módulos 2-8: Resumen Ejecutivo

Esta documentación cubre los módulos de frontend de forma concisa. Cada módulo sigue la misma estructura base del Core.

---

## Módulo 2: Auth (Autenticación)

### Responsabilidades
- Login/Logout
- Registro de usuarios
- Password reset
- Email verification
- Gestión de tokens

### Estructura
```
src/auth/
├── pages/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── ForgotPasswordPage.tsx
│   └── ResetPasswordPage.tsx
├── components/
│   ├── LoginForm.tsx
│   ├── RegisterForm.tsx
│   └── PasswordResetForm.tsx
├── api/
│   └── auth.api.ts
├── hooks/
│   ├── useLogin.ts
│   ├── useRegister.ts
│   └── usePasswordReset.ts
└── types/
    └── auth.types.ts
```

### Componentes Clave

**LoginPage.tsx**
```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLogin } from '../hooks/useLogin';
import { Button } from '@/core/components/ui/button';
import { Input } from '@/core/components/ui/input';
import { Form } from '@/core/components/ui/form';

const loginSchema = z.object({
  email: z.string().email('Email inválido'),
  password: z.string().min(8, 'Mínimo 8 caracteres'),
});

export function LoginPage() {
  const form = useForm({
    resolver: zodResolver(loginSchema),
  });

  const { mutate: login, isLoading } = useLogin();

  const onSubmit = (data: z.infer<typeof loginSchema>) => {
    login(data);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <h2 className="text-3xl font-bold text-center">Iniciar Sesión</h2>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <Input {...form.register('email')} placeholder="Email" />
            <Input {...form.register('password')} type="password" placeholder="Contraseña" />
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Iniciando...' : 'Iniciar Sesión'}
            </Button>
          </form>
        </Form>
      </div>
    </div>
  );
}
```

**useLogin.ts**
```typescript
import { useMutation } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/auth.api';
import { useAuthStore } from '@/core/hooks/useAuth';
import { toast } from 'sonner';

export function useLogin() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (response) => {
      setAuth(response.user, response.tokens.accessToken);
      toast.success('Inicio de sesión exitoso');
      navigate('/');
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Error al iniciar sesión');
    },
  });
}
```

**auth.api.ts**
```typescript
import { apiClient } from '@/core/api/client';

export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const { data } = await apiClient.post('/auth/login', credentials);
    return data;
  },

  register: async (userData: RegisterData) => {
    const { data } = await apiClient.post('/auth/register', userData);
    return data;
  },

  logout: async (refreshToken: string) => {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
  },

  requestPasswordReset: async (email: string) => {
    await apiClient.post('/auth/password-reset/request', { email });
  },

  resetPassword: async (token: string, newPassword: string) => {
    await apiClient.post('/auth/password-reset/confirm', { token, new_password: newPassword });
  },
};
```

---

## Módulo 3: Dashboard

### Responsabilidades
- Vista de empleado (sus onboardings)
- Vista de admin (métricas generales)
- Widgets de progreso
- Accesos rápidos

### Componentes Clave

**DashboardPage.tsx**
```typescript
import { useAuth } from '@/core/hooks/useAuth';
import { EmployeeDashboard } from '../components/EmployeeDashboard';
import { AdminDashboard } from '../components/AdminDashboard';

export function DashboardPage() {
  const { user } = useAuth();

  const isAdmin = user?.role === 'tenant_admin' || user?.role === 'super_admin';

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      {isAdmin ? <AdminDashboard /> : <EmployeeDashboard />}
    </div>
  );
}
```

**EmployeeDashboard.tsx**
```typescript
import { useQuery } from '@tanstack/react-query';
import { onboardingApi } from '@/onboarding/api/onboarding.api';
import { OnboardingCard } from '@/onboarding/components/OnboardingCard';
import { Progress } from '@/core/components/ui/progress';

export function EmployeeDashboard() {
  const { data: assignments, isLoading } = useQuery({
    queryKey: ['my-assignments'],
    queryFn: onboardingApi.getMyAssignments,
  });

  if (isLoading) return <LoadingSpinner />;

  const inProgress = assignments?.filter(a => a.status === 'in_progress') || [];
  const completed = assignments?.filter(a => a.status === 'completed') || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard title="En Progreso" value={inProgress.length} />
        <StatCard title="Completados" value={completed.length} />
        <StatCard title="Total" value={assignments?.length || 0} />
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Mis Onboardings</h2>
        <div className="space-y-4">
          {assignments?.map(assignment => (
            <OnboardingCard key={assignment.id} assignment={assignment} />
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Módulo 4: Tenant Settings

### Responsabilidades
- Configuración general del tenant
- Branding (logo, colores)
- Gestión de plan

### Componentes Clave

**TenantSettingsPage.tsx**
```typescript
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/core/components/ui/tabs';
import { GeneralSettings } from '../components/GeneralSettings';
import { BrandingSettings } from '../components/BrandingSettings';

export function TenantSettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Configuración</h1>

      <Tabs defaultValue="general">
        <TabsList>
          <TabsTrigger value="general">General</TabsTrigger>
          <TabsTrigger value="branding">Branding</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <GeneralSettings />
        </TabsContent>

        <TabsContent value="branding">
          <BrandingSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

**BrandingSettings.tsx**
```typescript
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { tenantApi } from '../api/tenant.api';
import { Button } from '@/core/components/ui/button';
import { Input } from '@/core/components/ui/input';
import { Label } from '@/core/components/ui/label';

export function BrandingSettings() {
  const queryClient = useQueryClient();
  const form = useForm();

  const { mutate: updateBranding } = useMutation({
    mutationFn: tenantApi.updateBranding,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenant'] });
      toast.success('Branding actualizado');
    },
  });

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const { url } = await tenantApi.uploadLogo(formData);
    updateBranding({ logo_url: url });
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <Label>Logo</Label>
        <Input type="file" accept="image/*" onChange={handleLogoUpload} />
      </div>

      <div>
        <Label>Color Primario</Label>
        <Input type="color" {...form.register('primary_color')} />
      </div>

      <div>
        <Label>Color Secundario</Label>
        <Input type="color" {...form.register('secondary_color')} />
      </div>

      <Button onClick={form.handleSubmit((data) => updateBranding(data))}>
        Guardar Cambios
      </Button>
    </div>
  );
}
```

---

## Módulo 5: Users (Gestión de Usuarios)

### Responsabilidades
- Listar usuarios del tenant
- Invitar nuevos usuarios
- Editar roles y perfiles
- Ver detalles de usuario

### Componentes Clave

**UsersPage.tsx**
```typescript
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { userApi } from '../api/user.api';
import { UserTable } from '../components/UserTable';
import { InviteUserDialog } from '../components/InviteUserDialog';
import { Button } from '@/core/components/ui/button';
import { Input } from '@/core/components/ui/input';
import { useDebounce } from '@/core/hooks/useDebounce';

export function UsersPage() {
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search);

  const { data, isLoading } = useQuery({
    queryKey: ['users', debouncedSearch],
    queryFn: () => userApi.list({ search: debouncedSearch }),
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Usuarios</h1>
        <InviteUserDialog />
      </div>

      <Input
        placeholder="Buscar usuarios..."
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {isLoading ? <LoadingSpinner /> : <UserTable users={data?.data || []} />}
    </div>
  );
}
```

**InviteUserDialog.tsx**
```typescript
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { userApi } from '../api/user.api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/core/components/ui/dialog';
import { Button } from '@/core/components/ui/button';
import { Input } from '@/core/components/ui/input';
import { Select } from '@/core/components/ui/select';

export function InviteUserDialog() {
  const [open, setOpen] = useState(false);
  const form = useForm();
  const queryClient = useQueryClient();

  const { mutate: inviteUser } = useMutation({
    mutationFn: userApi.invite,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      toast.success('Invitación enviada');
      setOpen(false);
      form.reset();
    },
  });

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>Invitar Usuario</Button>
      </DialogTrigger>

      <DialogContent>
        <DialogHeader>
          <DialogTitle>Invitar Nuevo Usuario</DialogTitle>
        </DialogHeader>

        <form onSubmit={form.handleSubmit((data) => inviteUser(data))} className="space-y-4">
          <Input {...form.register('email')} placeholder="Email" />

          <Select {...form.register('role')}>
            <option value="employee">Empleado</option>
            <option value="tenant_admin">Admin</option>
          </Select>

          <Button type="submit" className="w-full">Enviar Invitación</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
```

---

## Módulo 6: Onboarding (Crítico)

### Responsabilidades

**Empleado:**
- Ver onboardings asignados
- Completar módulos (texto, video, quiz)
- Tracking de progreso

**Admin:**
- Crear/editar flujos
- Crear módulos
- Asignar a empleados
- Ver progreso de todos

### Estructura
```
src/onboarding/
├── employee/              # Vista empleado
│   ├── pages/
│   │   ├── MyOnboardingsPage.tsx
│   │   └── OnboardingDetailPage.tsx
│   └── components/
│       ├── ModuleViewer.tsx
│       ├── QuizModule.tsx
│       └── VideoModule.tsx
├── admin/                 # Vista admin
│   ├── pages/
│   │   ├── FlowsListPage.tsx
│   │   ├── FlowEditorPage.tsx
│   │   └── AssignmentsPage.tsx
│   └── components/
│       ├── FlowBuilder.tsx
│       ├── ModuleForm.tsx
│       └── AssignmentDialog.tsx
├── api/
│   └── onboarding.api.ts
└── types/
    └── onboarding.types.ts
```

### Componentes Clave (Empleado)

**OnboardingDetailPage.tsx**
```typescript
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingApi } from '../../api/onboarding.api';
import { ModuleViewer } from '../components/ModuleViewer';
import { Progress } from '@/core/components/ui/progress';
import { Card } from '@/core/components/ui/card';

export function OnboardingDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();

  const { data: assignment } = useQuery({
    queryKey: ['assignment', id],
    queryFn: () => onboardingApi.getAssignment(Number(id)),
  });

  const { mutate: completeModule } = useMutation({
    mutationFn: ({ moduleId, data }: any) =>
      onboardingApi.completeModule(Number(id), moduleId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assignment', id] });
      toast.success('Módulo completado');
    },
  });

  if (!assignment) return <LoadingSpinner />;

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <Card className="p-6">
        <h1 className="text-3xl font-bold mb-2">{assignment.flowTitle}</h1>
        <Progress value={assignment.completionPercentage} className="h-2" />
        <p className="text-sm text-gray-600 mt-2">
          {assignment.completionPercentage}% Completado
        </p>
      </Card>

      <div className="space-y-4">
        {assignment.moduleProgress?.map((progress) => (
          <ModuleViewer
            key={progress.moduleId}
            progress={progress}
            onComplete={(data) => completeModule({ moduleId: progress.moduleId, data })}
          />
        ))}
      </div>
    </div>
  );
}
```

**QuizModule.tsx**
```typescript
import { useState } from 'react';
import { Button } from '@/core/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/core/components/ui/radio-group';
import { Card } from '@/core/components/ui/card';

interface QuizModuleProps {
  module: any;
  onSubmit: (answers: Record<string, string>) => void;
}

export function QuizModule({ module, onSubmit }: QuizModuleProps) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const questions = module.quizData?.questions || [];

  const handleSubmit = () => {
    onSubmit({ answers });
  };

  return (
    <Card className="p-6">
      <h3 className="text-xl font-semibold mb-4">{module.title}</h3>

      <div className="space-y-6">
        {questions.map((question: any, index: number) => (
          <div key={index}>
            <p className="font-medium mb-2">{question.question}</p>
            <RadioGroup
              value={answers[index]}
              onValueChange={(value) => setAnswers({ ...answers, [index]: value })}
            >
              {question.options.map((option: string) => (
                <div key={option} className="flex items-center space-x-2">
                  <RadioGroupItem value={option} id={`${index}-${option}`} />
                  <label htmlFor={`${index}-${option}`}>{option}</label>
                </div>
              ))}
            </RadioGroup>
          </div>
        ))}
      </div>

      <Button onClick={handleSubmit} className="mt-6">
        Enviar Quiz
      </Button>
    </Card>
  );
}
```

### Componentes Clave (Admin)

**FlowEditorPage.tsx**
```typescript
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { onboardingApi } from '../../api/onboarding.api';
import { FlowBuilder } from '../components/FlowBuilder';
import { ModuleForm } from '../components/ModuleForm';
import { Button } from '@/core/components/ui/button';
import { Plus } from 'lucide-react';

export function FlowEditorPage() {
  const { id } = useParams();
  const [showModuleForm, setShowModuleForm] = useState(false);
  const queryClient = useQueryClient();

  const { data: flow } = useQuery({
    queryKey: ['flow', id],
    queryFn: () => onboardingApi.getFlow(Number(id)),
  });

  const { mutate: createModule } = useMutation({
    mutationFn: (data: any) => onboardingApi.createModule(Number(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['flow', id] });
      setShowModuleForm(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">{flow?.title}</h1>
        <Button onClick={() => setShowModuleForm(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Agregar Módulo
        </Button>
      </div>

      <FlowBuilder flow={flow} />

      {showModuleForm && (
        <ModuleForm
          onSubmit={createModule}
          onCancel={() => setShowModuleForm(false)}
        />
      )}
    </div>
  );
}
```

---

## Módulo 7: Content (CMS)

### Responsabilidades
- CRUD de bloques de contenido
- Upload de archivos
- Categorización

### Componentes Clave

**ContentListPage.tsx**
```typescript
import { useQuery } from '@tanstack/react-query';
import { contentApi } from '../api/content.api';
import { ContentCard } from '../components/ContentCard';
import { CreateContentDialog } from '../components/CreateContentDialog';

export function ContentListPage() {
  const { data } = useQuery({
    queryKey: ['content'],
    queryFn: contentApi.list,
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between">
        <h1 className="text-3xl font-bold">Contenido</h1>
        <CreateContentDialog />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {data?.data.map(block => (
          <ContentCard key={block.id} block={block} />
        ))}
      </div>
    </div>
  );
}
```

---

## Módulo 8: Analytics (Reportes)

### Responsabilidades
- Dashboard de métricas
- Gráficos de progreso
- Reportes por flujo

### Componentes Clave

**AnalyticsPage.tsx**
```typescript
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics.api';
import { OverviewCards } from '../components/OverviewCards';
import { CompletionChart } from '../components/CompletionChart';
import { FlowAnalyticsTable } from '../components/FlowAnalyticsTable';

export function AnalyticsPage() {
  const { data: overview } = useQuery({
    queryKey: ['analytics-overview'],
    queryFn: analyticsApi.getDashboard,
  });

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Analytics</h1>

      <OverviewCards data={overview} />
      <CompletionChart />
      <FlowAnalyticsTable />
    </div>
  );
}
```

**CompletionChart.tsx**
```typescript
import { useQuery } from '@tanstack/react-query';
import { analyticsApi } from '../api/analytics.api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

export function CompletionChart() {
  const { data } = useQuery({
    queryKey: ['completion-trends'],
    queryFn: () => analyticsApi.getTrends({
      startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      endDate: new Date(),
    }),
  });

  return (
    <div className="bg-white p-6 rounded-lg">
      <h3 className="text-lg font-semibold mb-4">Tendencia de Completación</h3>
      <LineChart width={800} height={300} data={data?.trends}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Line type="monotone" dataKey="completions" stroke="#3B82F6" />
      </LineChart>
    </div>
  );
}
```

---

## Checklist General de Módulos Frontend

### Auth
- [ ] Login/Register pages con validación
- [ ] Password reset flow
- [ ] Token management en store
- [ ] Logout functionality

### Dashboard
- [ ] Vista empleado con sus assignments
- [ ] Vista admin con métricas
- [ ] Widgets de estadísticas
- [ ] Responsive design

### Tenant Settings
- [ ] General settings form
- [ ] Branding config (logo, colores)
- [ ] Upload de archivos
- [ ] Preview de cambios

### Users
- [ ] Lista con search y filtros
- [ ] Invite user dialog
- [ ] User detail/edit
- [ ] Role management

### Onboarding
- [ ] Employee: ver y completar onboardings
- [ ] Admin: crear/editar flujos
- [ ] Module viewer (text, video, quiz, PDF)
- [ ] Progress tracking visual
- [ ] Assignment management

### Content
- [ ] CRUD de content blocks
- [ ] Upload de media
- [ ] Categorías y tags
- [ ] Search functionality

### Analytics
- [ ] Dashboard con KPIs
- [ ] Charts (completion, trends)
- [ ] Tables de reportes
- [ ] Filtros por fecha

---

## Notas Finales

1. **Orden de Desarrollo:** Core → Auth → Dashboard → Users → Tenant Settings → Onboarding → Content → Analytics

2. **Testing:** Cada módulo debe tener tests con Vitest + React Testing Library

3. **Performance:**
   - Usar React.lazy() para code splitting
   - Optimizar imágenes
   - Cachear queries con React Query

4. **Accesibilidad:** shadcn/ui ya incluye accesibilidad, pero validar keyboard navigation

5. **Responsive:** Mobile-first approach con Tailwind

6. **Theming:** Aplicar colores del tenant en tiempo real con CSS variables

Esta documentación proporciona la base para que los desarrolladores implementen cada módulo de frontend de forma independiente y coordinada con el backend.

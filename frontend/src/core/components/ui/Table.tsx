import { type ReactNode } from 'react';
import { Table as BsTable, Pagination } from 'react-bootstrap';
import { ChevronUp, ChevronDown, ChevronsUpDown } from 'lucide-react';
import { Spinner } from './Spinner';
import type { TableColumn, SortConfig, PaginationConfig } from '@/core/types';

interface TableProps<T> {
  data: T[];
  columns: TableColumn<T>[];
  isLoading?: boolean;
  emptyMessage?: string;
  sortConfig?: SortConfig;
  onSort?: (key: string) => void;
  pagination?: PaginationConfig;
  onPageChange?: (page: number) => void;
  onRowClick?: (item: T) => void;
  rowKey: keyof T;
}

export function Table<T>({
  data,
  columns,
  isLoading,
  emptyMessage = 'No hay datos disponibles',
  sortConfig,
  onSort,
  pagination,
  onPageChange,
  onRowClick,
  rowKey,
}: TableProps<T>) {
  const renderSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ChevronsUpDown className="ms-1" size={14} style={{ opacity: 0.5 }} />;
    }
    return sortConfig.direction === 'asc' ? (
      <ChevronUp className="ms-1" size={14} />
    ) : (
      <ChevronDown className="ms-1" size={14} />
    );
  };

  const renderCell = (item: T, column: TableColumn<T>): ReactNode => {
    if (column.render) {
      return column.render(item);
    }
    const value = item[column.key as keyof T];
    if (value === null || value === undefined) return '-';
    return String(value);
  };

  const totalPages = pagination ? Math.ceil(pagination.total / pagination.pageSize) : 0;

  return (
    <div className="w-100">
      <BsTable hover responsive>
        <thead className="table-light">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={column.sortable ? 'cursor-pointer user-select-none' : ''}
                onClick={() => column.sortable && onSort?.(String(column.key))}
                style={{ cursor: column.sortable ? 'pointer' : 'default' }}
              >
                <div className="d-flex align-items-center">
                  {column.header}
                  {column.sortable && renderSortIcon(String(column.key))}
                </div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-5">
                <Spinner />
              </td>
            </tr>
          ) : data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-5 text-muted">
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((item) => (
              <tr
                key={String(item[rowKey])}
                onClick={() => onRowClick?.(item)}
                style={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {columns.map((column) => (
                  <td key={String(column.key)}>
                    {renderCell(item, column)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </BsTable>

      {pagination && totalPages > 1 && (
        <div className="d-flex justify-content-between align-items-center mt-3">
          <p className="text-muted small mb-0">
            Mostrando {(pagination.page - 1) * pagination.pageSize + 1} a{' '}
            {Math.min(pagination.page * pagination.pageSize, pagination.total)} de{' '}
            {pagination.total} resultados
          </p>
          <Pagination className="mb-0">
            <Pagination.Prev
              onClick={() => onPageChange?.(pagination.page - 1)}
              disabled={pagination.page === 1}
            />
            <Pagination.Item active>{pagination.page}</Pagination.Item>
            <Pagination.Next
              onClick={() => onPageChange?.(pagination.page + 1)}
              disabled={pagination.page === totalPages}
            />
          </Pagination>
        </div>
      )}
    </div>
  );
}

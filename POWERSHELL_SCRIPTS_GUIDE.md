# 🔷 Guia dos Scripts PowerShell

Este projeto inclui versões PowerShell de todos os scripts de benchmark para usuários Windows.

## 📋 Scripts Disponíveis

### 1. **test_benchmark.ps1**
Script rápido para testar se tudo está funcionando.

```powershell
.\test_benchmark.ps1
```

### 2. **run_optimized_benchmark.ps1**
Script interativo com menu para executar benchmarks otimizados.

```powershell
.\run_optimized_benchmark.ps1
```

Oferece opções para:
- Escolher tipo de teste (rápido, escalabilidade, carga completa)
- Selecionar bancos específicos
- Reiniciar containers com otimizações
- Ver resultados ao final

### 3. **run_all_benchmarks.ps1**
Executa todos os testes em todos os bancos automaticamente.

```powershell
.\run_all_benchmarks.ps1
```

## 🚀 Como Usar

### Pré-requisitos

1. **PowerShell 5.0+** (vem com Windows 10/11)
2. **Docker Desktop** instalado e rodando
3. **Python 3.8+** instalado
4. Dependências Python instaladas:
   ```powershell
   pip install -r requirements.txt
   ```

### Execução Rápida

1. Abra o PowerShell como usuário normal (não precisa ser admin)
2. Navegue até a pasta do projeto:
   ```powershell
   cd C:\caminho\para\db-benchmark
   ```
3. Execute o teste rápido:
   ```powershell
   .\test_benchmark.ps1
   ```
4. Se tudo funcionou, execute o benchmark completo:
   ```powershell
   .\run_optimized_benchmark.ps1
   ```

## 🎨 Características dos Scripts PowerShell

- **Interface Colorida**: Usa cores para melhor visualização
- **Menus Interativos**: Fácil escolha de opções
- **Validação de Erros**: Verifica se Docker está rodando
- **Relatórios Automáticos**: Gera e exibe resultados
- **Opção de Abrir Resultados**: Abre pasta de gráficos no Explorer

## 🛠️ Troubleshooting

### "Cannot be loaded because running scripts is disabled"

Se receber este erro, execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Docker não está rodando

Certifique-se de que o Docker Desktop está iniciado. O script verifica automaticamente.

### Comando não encontrado

Se `docker compose` não funcionar, tente:
```powershell
docker-compose --version
```

Se funcionar, edite os scripts e substitua `docker compose` por `docker-compose`.

## 📊 Visualizando Resultados

Após executar os benchmarks:

1. **Automático**: O script mostra um resumo no terminal
2. **Gráficos**: Use a opção do menu para abrir a pasta de visualizações
3. **Manual**: Navegue para `results\visualizations\`

## 💡 Dicas

- **Teste Rápido**: Use opção 1 (1000 registros) para validar setup
- **Teste Completo**: Use opção 3 (50k registros) para resultados reais
- **Foco em Banco Específico**: Use opção 5 do menu de bancos

## 🔄 Equivalência com Scripts Bash

| Script Bash | Script PowerShell | Descrição |
|-------------|-------------------|-----------|
| `test_benchmark.sh` | `test_benchmark.ps1` | Teste rápido |
| `run_optimized_benchmark.sh` | `run_optimized_benchmark.ps1` | Benchmark interativo |
| `run_all_benchmarks.sh` | `run_all_benchmarks.ps1` | Benchmark completo |

## 📝 Exemplo de Sessão Completa

```powershell
# 1. Abrir PowerShell
# 2. Navegar para o projeto
cd C:\Users\SeuUsuario\projetos\db-benchmark

# 3. Verificar Docker
docker ps

# 4. Teste rápido
.\test_benchmark.ps1

# 5. Se OK, benchmark otimizado
.\run_optimized_benchmark.ps1
# Escolher: 2 (10k registros)
# Escolher: 1 (todos os bancos)
# Aguardar conclusão

# 6. Ver resultados
# O script oferece opção de abrir pasta de gráficos
``` 
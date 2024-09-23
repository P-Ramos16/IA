import math

#Exercicio 4.1
impar = lambda a: a%2 == 1

#Exercicio 4.2
positivo = lambda a: a > 0 

#Exercicio 4.3
comparar_modulo = lambda x, y: abs(x) < abs(y) 

#Exercicio 4.4
cart2pol = lambda x, y: ((x**2+y**2)**(1/2), math.atan2(y, x))

#Exercicio 4.5
ex5 = lambda f, g, h: lambda x, y, z: h(f(x, y), g(y, z))

#Exercicio 4.6
def quantificador_universal(lista, f):
    if lista == []:
        return True  
    
    return f(lista[0]) and quantificador_universal(lista[1:], f)

#Exercicio 4.7
def quantificador_existencial(lista, f):
    if lista == []:
        return True  
    
    return f(lista[0]) or quantificador_existencial(lista[1:], f)

#Exercicio 4.8
def subconjunto(lista1, lista2):
    return quantificador_universal(lista1, lambda a1: a1 in lista2)

#Exercicio 4.9
def menor_ordem(lista, f):
    if not lista[1]:
        return lista[0]
    
    tail = menor_ordem(lista[1:], f)
    
    if f(lista[0], tail):
        return lista[0]
    else:
        return tail
    
    #  Single line
    #return lista[0] if f(lista[0], tail) else tail

#Exercicio 4.10
def menor_e_resto_ordem(lista, f):
    if lista == []:
        return (None, [])      
    
    if len(lista) < 2:
        return (lista[0], [])
    
    (smallest_tail, tail) = menor_e_resto_ordem(lista[1:], f)
    
    if f(lista[0], smallest_tail):
        return (lista[0], tail + [smallest_tail])
    else:
        return (smallest_tail, [lista[0]] + tail )

#Exercicio 5.2
def ordenar_seleccao(lista, ordem):
    if lista == []:
        return []      
    
    menor, tail = menor_e_resto_ordem(lista, ordem)
    
    return [menor] + ordenar_seleccao(tail, ordem)
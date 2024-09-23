#Exercicio 1.1
def comprimento(lista):
    if lista == []:
        return 0
    
    return 1 + comprimento(lista[1:])

#Exercicio 1.2
def soma(lista):
    if lista == []:
        return 0
    
    return lista[0] + soma(lista[1:])

#Exercicio 1.3
def existe(lista, elem):
    if lista == []:
        return False
    
    if lista[0] == elem:
        return True
    
    return existe(lista[1:], elem)

#Exercicio 1.4
def concat(l1, l2):
	if l1 == None:
		return concat([l2[0]], l2[1:])

	if l2 == []:
		return l1

	return concat(l1 + [l2[0]], l2[1:])

#Exercicio 1.5
def inverte(lista):
	if lista == []:
		return lista

	return concat(inverte(lista[1:]), [lista[0]])

#Exercicio 1.6
def capicua(lista):    
	""" OU return lista == inverte(lista) """
        
	if lista == []:
		return True

	if lista[0] != lista[-1]:
		return False

	return capicua(lista[1:-1])

#Exercicio 1.7
def concat_listas(lista):
	if lista == []:
		return []

	return concat(lista[0], concat_listas(lista[1:]))

#Exercicio 1.8
def substitui(lista, original, novo):
    if lista == []:
        return []
    
    val = lista[0]
    if lista[0] == original:
        val = novo
    
    return concat([val], substitui(lista[1:], original, novo))

#Exercicio 1.9
def fusao_ordenada(lista1, lista2):
	if lista1 == []:
		return lista2

	if lista2 == []:
		return lista1

	if lista1[0] < lista2[0]:
		return concat([lista1[0]], fusao_ordenada(lista1[1:], lista2))

	return concat([lista2[0]], fusao_ordenada(lista1, lista2[1:]))

#Exercicio 1.10
def lista_subconjuntos(lista):
    if lista == []:
        return [[]]
    
    listaFinal = lista_subconjuntos(lista[1:])
        
    listaFinal = concat(listaFinal, [[lista[0]] + val for val in listaFinal])
    
    return listaFinal 


#Exercicio 2.1
def separar(lista):
    if lista == []:
        return [], []
    
    a1, b1 = lista[0]
    tail_a, tail_b = separar(lista[1:])
    
    return [a1] + tail_a, [b1] + tail_b

#Exercicio 2.2
def remove_e_conta(lista, elem):
    if lista == []:
        return ([], 0)

    a1 = lista[0]
    tail = lista[1:]
    
    new_tail, num_elem =  remove_e_conta(tail, elem)
    
    if a1 == elem:
        return (new_tail, 1 + num_elem)
    else:
        return (concat([a1], new_tail), num_elem)


#Exercicio 3.1
def cabeca(lista):
    if lista == []:
        return None
    
    return lista[0]

#Exercicio 3.2
def cauda(lista):
    if lista == []:
        return None
    
    return lista[1:]

#Exercicio 3.3
def juntar(l1, l2):
    if comprimento(l1) != comprimento(l2):
        return None
    
    if l1 == [] and l2 == []:
        return []
    
    
    a1 = l1[0]
    b1 = l2[0]
    
    return [(a1, b1)] + juntar (l1[1:], l2[1:])

#Exercicio 3.4
def menor(lista):
    if lista == []:
        return None
    
    a1 = lista[0]
    tail = menor(lista[1:])
    
    if tail == None:
        return a1
    
    elif tail > a1:
        return a1
    
    else:
        return tail

#Exercicio 3.6
def max_min(lista):
    if lista == []:
        return None
    
    a1 = lista[0]
    b1 = lista[0]    
    
    tail = max_min(lista[1:])
    
    if tail == None:
        return (a1, b1)
    
    max = tail[0]
    min = tail[1]    
    
    if max > a1:
        if min < b1:
            return (max, min)
        else:
            return (max, b1)
    else:
        if min < b1:
            return (a1, min)
        else:
            return (a1, b1)
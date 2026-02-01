import pygame
import random
import time
from collections import deque

pygame.init()
ANCHO, ALTO, ANCHO_IZQ, TABLERO_SUP, CELDA, TABLERO_IZQ, PROFUNDIDAD_MAX, puntaje_jugador, puntaje_ia, MAX_TRAZA=900, 640, 440, 120, 120, 40, 9, 0, 0, 14
PANTALLA=pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("3 EN RAYA")
FONDO, PANEL=(12, 12, 30), (10, 10, 20)
NEON_CIAN, NEON_ROSA, NEON_AMARILLO, BLANCO, GRIS=(0, 255, 230), (255, 20, 147), (255, 240, 20), (245, 245, 245), (90, 90, 100)
ANCHO_DER=ANCHO-ANCHO_IZQ
TAM_TABLERO=CELDA*3
fuente_grande=pygame.font.SysFont(None, 56)
fuente_media=pygame.font.SysFont(None, 26)
fuente_peque=pygame.font.SysFont(None, 20)
tablero=[" " for _ in range(9)]
JUGADOR="X"
IA="O"
jugador_empieza, turno_jugador=True, True
icono_jugador=pygame.image.load("usuario.png").convert_alpha()
icono_robot=pygame.image.load("robot.png").convert_alpha()
icono_jugador=pygame.transform.smoothscale(icono_jugador,(64, 64))
icono_robot=pygame.transform.smoothscale(icono_robot,(64, 64))
ESTADO_MENU="menu"
ESTADO_JUGANDO="jugando"
ESTADO_FIN="fin"
estado, rects_menu, linea_ganadora=ESTADO_MENU, None, None
mensaje_fin=""
traza=[]
Q_TABLE = {}
ALPHA=0.1
GAMMA=0.9
EPSILON_TRAIN=0.3
TOTAL_EPISODIOS=0

class NodoArbol:
    def __init__(self, lista_tablero, mov_padre=None, jugador_turno=None):
        self.tablero=lista_tablero[:]
        self.movimiento=mov_padre
        self.jugador=jugador_turno
        self.hijos=[]
        self.valor=None
        self.id=id(self)

def movimientos_disponibles(tab):
    return [i for i, v in enumerate(tab) if v==" "]

def combinaciones_ganadoras():
    return [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]

def hay_ganador(tab, jugador):
    return any(all(tab[i]==jugador for i in combo) for combo in combinaciones_ganadoras())

def linea_ganadora_tablero(tab):
    for combo in combinaciones_ganadoras():
        a,b,c=combo
        if tab[a]!=" " and tab[a]==tab[b]==tab[c]:
            return combo
    return None

def tablero_a_str(tab):
    return "".join(tab)

def get_q(turno, state, action):
    return Q_TABLE.get((turno, state, action), 0.0)

def entrenar_ia():
    global Q_TABLE, TOTAL_EPISODIOS, traza
    ALPHA=0.5
    GAMMA=0.75
    NUEVOS_EPISODIOS=120000
    print(f"Entrenamiento")
    total_wins_x=0
    total_wins_o=0
    total_draws=0
    entrenamiento_start_time = time.time() 
    
    for ep in range(1, NUEVOS_EPISODIOS+1):
        if ep%100==0:
            pygame.event.pump()
        temp_tab=[" "]*9
        done=False
        turn="X"
        
        last_s_x, last_a_x=None, None
        last_s_o, last_a_o=None, None
        
        while not done:
            movs=movimientos_disponibles(temp_tab)
            state_str=tablero_a_str(temp_tab)
            qs=[get_q(turn, state_str, m) for m in movs]
            max_current_q=max(qs) if qs else 0.0
            if turn=="X" and last_s_x is not None:
                old_val=get_q("X", last_s_x, last_a_x)
                new_val=(1-ALPHA)*old_val+ALPHA*(0+GAMMA*max_current_q)
                Q_TABLE[("X", last_s_x, last_a_x)]=new_val
            elif turn=="O" and last_s_o is not None:
                old_val=get_q("O", last_s_o, last_a_o)
                new_val=(1-ALPHA)*old_val+ALPHA*(0+GAMMA*max_current_q)
                Q_TABLE[("O", last_s_o, last_a_o)]=new_val
            if random.random()<EPSILON_TRAIN:
                action=random.choice(movs)
            else:
                best_actions=[m for m, q in zip(movs, qs) if q==max_current_q]
                action=random.choice(best_actions)
            temp_tab[action] = turn

            if hay_ganador(temp_tab, turn):
                done=True
                Q_TABLE[(turn, state_str, action)]=(1-ALPHA)*get_q(turn, state_str, action)+ALPHA*1.0
                if turn=="X":
                    total_wins_x+=1
                    if last_s_o:Q_TABLE[("O", last_s_o, last_a_o)]=(1-ALPHA)*get_q("O", last_s_o, last_a_o)+ALPHA*-1.0
                else:
                    total_wins_o+=1
                    if last_s_x:Q_TABLE[("X", last_s_x, last_a_x)]=(1-ALPHA)*get_q("X", last_s_x, last_a_x)+ALPHA*-1.0
            elif not movimientos_disponibles(temp_tab):
                done=True
                total_draws+=1
                Q_TABLE[(turn, state_str, action)]=(1-ALPHA)*get_q(turn, state_str, action)+ALPHA*0.0
                if last_s_x:Q_TABLE[("X", last_s_x, last_a_x)]=(1-ALPHA)*get_q("X", last_s_x, last_a_x)+ALPHA*0.0
                if last_s_o:Q_TABLE[("O", last_s_o, last_a_o)]=(1-ALPHA)*get_q("O", last_s_o, last_a_o)+ALPHA*0.0
            else:
                if turn=="X":
                    last_s_x, last_a_x, turn=state_str, action, "O"
                else:
                    last_s_o, last_a_o, turn=state_str, action, "X"

        if ep%5000==0:
            tiempo_total=time.time()-entrenamiento_start_time
            print(f"Ep: {TOTAL_EPISODIOS+ep:7} | V.X: {total_wins_x:5} | V.O: {total_wins_o:5} | Empates: {total_draws:5} | Time: {tiempo_total:.1f}s")

    TOTAL_EPISODIOS+=NUEVOS_EPISODIOS
    traza.append(f"Entrenamiento completo: {TOTAL_EPISODIOS} eps.")

def mejor_jugada_con_arbol(tablero_actual, simbolo_ia):
    raiz=NodoArbol(tablero_actual, mov_padre=None, jugador_turno=simbolo_ia)

    movs=movimientos_disponibles(tablero_actual)
    state_str=tablero_a_str(tablero_actual)

    qs_visuales=[]
    for m in movs:
        val=get_q(simbolo_ia, state_str, m)
        qs_visuales.append((m, val))
        nt=tablero_actual[:]
        nt[m]=simbolo_ia
        hijo=NodoArbol(nt, mov_padre=m, jugador_turno=None)
        hijo.valor=round(val, 4)
        raiz.hijos.append(hijo)

    mejor_mov=None
    if qs_visuales:
        qs_visuales.sort(key=lambda x: x[1], reverse=True)
        max_q=qs_visuales[0][1]
        mejores=[pair[0] for pair in qs_visuales if pair[1] == max_q]
        mejor_mov=random.choice(mejores)
        val_elegido=max_q
    else:
        mejor_mov=None
        val_elegido=0

    return mejor_mov, raiz

def dibujar_linea_brillante(superficie, color, inicio, fin, ancho, capas=5):
    for i in range(capas,0,-1):
        s=pygame.Surface((ANCHO_IZQ, ALTO), pygame.SRCALPHA)
        a=max(12,int(255*(i/(capas+1))*0.5))
        col=(color[0], color[1], color[2], a)
        pygame.draw.line(s, col, inicio, fin, ancho+i*2)
        superficie.blit(s,(0,0))
    pygame.draw.line(superficie, color, inicio, fin, ancho)

def dibujar_tablero(superficie):
    pygame.draw.rect(superficie, PANEL, (TABLERO_IZQ-8, TABLERO_SUP-8, TAM_TABLERO+16, TAM_TABLERO+16), border_radius=8)
    for i in range(1,3):
        x=TABLERO_IZQ+i*CELDA
        pygame.draw.line(superficie, NEON_CIAN, (x, TABLERO_SUP), (x, TABLERO_SUP + TAM_TABLERO), 6)
    for i in range(1,3):
        y=TABLERO_SUP+i*CELDA
        pygame.draw.line(superficie, NEON_CIAN, (TABLERO_IZQ, y), (TABLERO_IZQ + TAM_TABLERO, y), 6)
    fuente_grande_negrita=pygame.font.SysFont(None, 120, bold=True)
    for idx, val in enumerate(tablero):
        if val!=" ":
            fila,col=divmod(idx, 3)
            cx=TABLERO_IZQ+col*CELDA+CELDA//2
            cy=TABLERO_SUP+fila*CELDA+CELDA//2
            color=NEON_AMARILLO if val=="X" else NEON_ROSA
            texto=fuente_grande_negrita.render(val, True, color)
            rect=texto.get_rect(center=(cx, cy))
            superficie.blit(texto, rect)

def dibujar_panel_superior(superficie):
    pygame.draw.rect(superficie,PANEL,(0,0,ANCHO_IZQ,100))
    jx,jy=250,20
    rx,ry=20,20
    superficie.blit(icono_jugador,(jx,jy))
    txt_j=fuente_media.render(f" Tú ({JUGADOR})",True,BLANCO)
    superficie.blit(txt_j,(jx+80,jy+10))
    scr_j=fuente_media.render(str(puntaje_jugador),True,NEON_CIAN)
    superficie.blit(scr_j,(jx+80,jy+36))
    superficie.blit(icono_robot,(rx,ry))
    txt_ai=fuente_media.render(f" IA ({IA})",True,BLANCO)
    superficie.blit(txt_ai,(rx+80,ry+10))
    scr_ai=fuente_media.render(str(puntaje_ia),True,NEON_ROSA)
    superficie.blit(scr_ai,(rx+80,ry+36))

def dibujar_pie(superficie, mensaje="", mostrar_reintentar=False):
    pygame.draw.rect(superficie, PANEL, (0, ALTO-80, ANCHO_IZQ, 80))
    if mensaje:
        msg=fuente_media.render(mensaje, True, BLANCO)
        superficie.blit(msg, (20, ALTO-64))
    if mostrar_reintentar:
        ancho_btn, alto_btn=100, 40
        bx=ANCHO_IZQ-ancho_btn-20
        by=ALTO-60
        pygame.draw.rect(superficie, NEON_CIAN, (bx, by, ancho_btn, alto_btn), border_radius=8)
        txt=fuente_media.render("Volver", True, (10, 10, 12))
        superficie.blit(txt, (bx+12, by+8))

def dibujar_linea_ganadora(superficie, combo):
    if not combo: return
    a,b,c=combo
    af,ac=divmod(a,3)
    cf,cc=divmod(c,3)
    ax=TABLERO_IZQ+ac*CELDA+CELDA//2
    ay=TABLERO_SUP+af*CELDA+CELDA//2
    cx_=TABLERO_IZQ+cc*CELDA+CELDA//2
    cy_=TABLERO_SUP+cf*CELDA+CELDA//2
    dibujar_linea_brillante(superficie, NEON_AMARILLO if tablero[a]==JUGADOR else NEON_ROSA, (ax,ay), (cx_,cy_), 12, capas=7)

def dibujar_mini_arbol(superficie, raiz, area):
    if not raiz or not raiz.hijos:
        return
    margen_x, margen_y=12, 12
    ancho_util, alto_util=area.width-2*margen_x, area.height-2*margen_y
    tam_celda=min(ancho_util//3, alto_util//3)
    if tam_celda<20:tam_celda=20
    cols=3
    filas=(len(raiz.hijos)+cols-1)//cols
    max_filas=3
    if filas>max_filas:
        filas=max_filas
        cols=(len(raiz.hijos)+filas-1)//filas
    ancho_celda=min(tam_celda, ancho_util//cols)
    alto_celda=min(tam_celda, (alto_util-50*(filas - 1)) // filas)
    espacio_x=(ancho_util-cols*ancho_celda)//(cols+1)
    for idx, hijo in enumerate(raiz.hijos):
        fila=idx//cols
        col=idx%cols
        x=area.x+margen_x+col*(ancho_celda+espacio_x)+espacio_x
        y=area.y+margen_y+fila*(alto_celda+50)
        dibujar_mini_tablero(superficie, hijo.tablero, x, y, ancho_celda, alto_celda)
        if hijo.valor is not None:
            texto_val=f"{hijo.valor:.2f}"
            color_val=NEON_ROSA if hijo.valor>0.5 else (NEON_CIAN if hijo.valor<0 else NEON_AMARILLO)
            surf_val=fuente_media.render(texto_val, True, color_val)
            rect_val=surf_val.get_rect(center=(x+ancho_celda//2, y+alto_celda+8))
            superficie.blit(surf_val, rect_val)

def dibujar_mini_tablero(superficie, estado_tablero, x, y, ancho, alto):
    pygame.draw.rect(superficie, (20, 20, 30), (x, y, ancho, alto), border_radius=4)
    for i in range(1, 3):
        lx=x+i*ancho//3
        ly=y+i*alto//3
        pygame.draw.line(superficie, GRIS, (lx, y), (lx, y + alto), 1)
        pygame.draw.line(superficie, GRIS, (x, ly), (x + ancho, ly), 1)
    for i in range(9):
        if estado_tablero[i]!=" ":
            fila, col=divmod(i, 3)
            cx=x+(col+0.5)*ancho//3
            cy=y+(fila+0.5)*alto//3
            color=NEON_AMARILLO if estado_tablero[i]=="X" else NEON_ROSA
            fuente_mini=pygame.font.SysFont(None, int(ancho / 3))
            texto=fuente_mini.render(estado_tablero[i], True, color)
            rect=texto.get_rect(center=(cx, cy))
            superficie.blit(texto, rect)

def dibujar_panel_derecho(superficie, raiz_arbol):
    rx=ANCHO_IZQ
    pygame.draw.rect(superficie, (8, 8, 14), (rx, 0, ANCHO_DER, ALTO))
    area_arbol=pygame.Rect(rx+12, 36, ANCHO_DER-24, ALTO//2-36)
    pygame.draw.rect(superficie, (6, 6, 12), area_arbol, border_radius=6)
    if raiz_arbol:
        dibujar_mini_arbol(superficie, raiz_arbol, area_arbol)
    area_traza=pygame.Rect(rx+12, ALTO//2+6, ANCHO_DER-24, ALTO//2-18)
    pygame.draw.rect(superficie, (6, 6, 12), area_traza, border_radius=6)
    
    start_y = area_traza.y + 10
    for i, t in enumerate(traza):
        txt = fuente_peque.render(t, True, BLANCO)
        superficie.blit(txt, (area_traza.x + 10, start_y + i * 20))

def pos_a_celda(mx, my):
    if mx<TABLERO_IZQ or mx>TABLERO_IZQ+TAM_TABLERO or my<TABLERO_SUP or my>TABLERO_SUP+TAM_TABLERO: return None
    col=(mx-TABLERO_IZQ)//CELDA
    fila=(my-TABLERO_SUP)//CELDA
    return int(fila*3+col)

def reiniciar_tablero():
    global tablero, linea_ganadora, mensaje_fin, traza
    tablero=[" " for _ in range(9)]
    linea_ganadora=None
    mensaje_fin=""
    traza=[]

def verificar_fin():
    global estado, mensaje_fin, puntaje_jugador, puntaje_ia, linea_ganadora
    if hay_ganador(tablero, JUGADOR):
        mensaje_fin="Has ganado la partida."
        puntaje_jugador+=1
        linea_ganadora=linea_ganadora_tablero(tablero)
        estado=ESTADO_FIN
    elif hay_ganador(tablero, IA):
        mensaje_fin="Ha ganado la IA."
        puntaje_ia+=1
        linea_ganadora=linea_ganadora_tablero(tablero)
        estado=ESTADO_FIN
    elif not movimientos_disponibles(tablero):
        mensaje_fin="Empate."
        linea_ganadora=None
        estado=ESTADO_FIN

def dibujar_menu(superficie):
    superficie.fill(FONDO)
    titulo=fuente_grande.render("3 EN RAYA", True, NEON_ROSA)
    rect_titulo=titulo.get_rect(center=(ANCHO // 2, 60))
    superficie.blit(titulo, rect_titulo)
    subtitulo=fuente_media.render("Elige tu ficha para empezar el juego.", True, BLANCO)
    rect_sub=subtitulo.get_rect(center=(ANCHO // 2, 110))
    superficie.blit(subtitulo, rect_sub)
    subtitulo2=fuente_media.render("El juego será IA Vs. Usuario.", True, BLANCO)
    rect_sub2=subtitulo2.get_rect(center=(ANCHO // 2, 140))
    superficie.blit(subtitulo2, rect_sub2)
    
    ancho_btn, alto_btn=140, 80
    total_ancho_btn=ancho_btn*2+30
    inicio_x=(ANCHO-total_ancho_btn)//2
    bx, by=inicio_x, 200

    rect_x=pygame.Rect(bx, by, ancho_btn, alto_btn)
    pygame.draw.rect(superficie, NEON_AMARILLO, rect_x, border_radius=10)
    txt_x=fuente_grande.render("X", True, (20,20,20))
    superficie.blit(txt_x, txt_x.get_rect(center=rect_x.center))

    bx2=bx+ancho_btn+30
    rect_o=pygame.Rect(bx2, by, ancho_btn, alto_btn)
    pygame.draw.rect(superficie, NEON_ROSA, rect_o, border_radius=10)
    txt_o=fuente_grande.render("O", True, (20,20,20))
    superficie.blit(txt_o, txt_o.get_rect(center=rect_o.center))

    by_train = by + alto_btn + 30
    ancho_train = total_ancho_btn
    alto_train = 50
    rect_train = pygame.Rect(bx, by_train, ancho_train, alto_train)
    pygame.draw.rect(superficie, NEON_CIAN, rect_train, border_radius=10)
    txt_train = fuente_media.render("Entrenamiento: IA vs IA", True, (20,20,20))
    superficie.blit(txt_train, txt_train.get_rect(center=rect_train.center))

    instruccion=fuente_peque.render("Si eliges la X tendrás el primer turno, si eliges la O tendrás el segundo turno.", True, GRIS)
    superficie.blit(instruccion, instruccion.get_rect(center=(ANCHO // 2, by_train + alto_train + 24)))
    
    return rect_x, rect_o, rect_train

running=True
raiz_arbol_cache=None
while running:
    mx, my=pygame.mouse.get_pos()
    clic=False
    for event in pygame.event.get():
        if event.type==pygame.QUIT:running=False
        if event.type==pygame.MOUSEBUTTONDOWN and event.button == 1: clic = True
    if estado==ESTADO_MENU:
        rect_x, rect_o, rect_train=dibujar_menu(PANTALLA)
        if clic:
            if rect_x.collidepoint((mx, my)):
                JUGADOR, IA, jugador_empieza, turno_jugador="X", "O", True, True
                reiniciar_tablero()
                estado=ESTADO_JUGANDO
                raiz_arbol_cache=None
            elif rect_o.collidepoint((mx, my)):
                JUGADOR, IA, jugador_empieza, turno_jugador="O", "X", False, False
                reiniciar_tablero()
                estado=ESTADO_JUGANDO
                raiz_arbol_cache=None
            elif rect_train.collidepoint((mx, my)):
                entrenar_ia()
                pass
        pygame.display.flip()
        continue
    PANTALLA.fill(FONDO)
    superficie_izq=PANTALLA.subsurface((0, 0, ANCHO_IZQ, ALTO))
    superficie_izq.fill(FONDO)
    dibujar_panel_superior(superficie_izq)
    dibujar_tablero(superficie_izq)
    if linea_ganadora: dibujar_linea_ganadora(superficie_izq, linea_ganadora)
    dibujar_panel_derecho(PANTALLA, raiz_arbol_cache)
    if estado==ESTADO_JUGANDO:
        if not turno_jugador:
            pygame.time.delay(180)
            if movimientos_disponibles(tablero):
                if IA=="X" and all(c==" " for c in tablero) and TOTAL_EPISODIOS==0:
                    mov=4
                    raiz_arbol_cache=None 
                else:
                    mov, raiz=mejor_jugada_con_arbol(tablero[:], IA)
                    raiz_arbol_cache=raiz
                
                if mov is not None and tablero[mov]==" ":
                    tablero[mov]=IA
                turno_jugador=True
                verificar_fin()
        else:
            if clic:
                celda=pos_a_celda(mx, my)
                if celda is not None and tablero[celda]==" ":
                    tablero[celda]=JUGADOR
                    turno_jugador=False
                    verificar_fin()
                    raiz_arbol_cache=None
    mostrar_reintentar=False
    mensaje_pie=""
    if estado==ESTADO_FIN:
        mensaje_pie=mensaje_fin
        mostrar_reintentar=True
    dibujar_pie(superficie_izq, mensaje_pie, mostrar_reintentar)
    if mostrar_reintentar and clic:
        ancho_btn, alto_btn=200,40
        bx=ANCHO_IZQ-ancho_btn-20
        by=ALTO-60
        if bx<=mx<=bx+ancho_btn and by<=my<=by+alto_btn:
            estado=ESTADO_MENU
            reiniciar_tablero()
            raiz_arbol_cache=None
    if len(traza)>MAX_TRAZA:
        traza=traza[-MAX_TRAZA:]
    pygame.display.flip()
pygame.quit()